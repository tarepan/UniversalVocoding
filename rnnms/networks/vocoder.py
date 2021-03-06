from torch.tensor import Tensor
import torch.nn as nn
import torch.nn.functional as F
from torchaudio.transforms import MuLawDecoding

from .decoder import C_eAR_GenRNN


class RNN_MS_Vocoder(nn.Module):
    """RNN_MS: Universal Vocoder
    """
    def __init__(
        self,
        size_mel_freq: int,
        size_latent: int,
        size_embed_ar: int,
        size_rnn_h: int,
        size_fc_h: int,
        bits_mu_law: int,
        hop_length: int,
    ):
        """Set up the hyperparams.

        Args:
            size_mel_freq: size of mel frequency dimension
            size_latent: size of latent vector
            size_embed_ar: size of embedded auto-regressive input vector (embedded sample_t-1)
            size_rnn_h: size of decoder's RNN hidden vector
            size_fc_h: size of decoder's FC hidden layer
            bits_mu_law: bit depth of μ-law encoding
            hop_length: STFT stride
        """

        super().__init__()
        self.hop_length = hop_length

        self.encoder = nn.GRU(size_mel_freq, size_latent, num_layers=2, batch_first=True, bidirectional=True)
        self.decoder = C_eAR_GenRNN(size_latent, size_embed_ar, size_rnn_h, size_fc_h, 2**bits_mu_law)
        self.mulaw_dec = MuLawDecoding(2**bits_mu_law)

    def forward(self, wave_mu_law: Tensor, mels: Tensor) -> Tensor:
        """Forward computation for training.
        
        Arguments:
            wave_mu_law: mu-law encoded waveform
            mels (Tensor(Batch, Time, Freq)): preprocessed mel-spectrogram
        
        Returns:
            Tensor(Batch, Time, before_softmax) Generated mu-law encoded waveform
        """
        # Encoding for conditioning
        # Tensor(batch, T_mel, 2*size_latent)
        latents, _ = self.encoder(mels)

        # Cond. Upsampling
        # Tensor(batch, T_mel*hop_length, 2*size_latent)
        latents_upsampled: Tensor = F.interpolate(latents.transpose(1, 2), scale_factor=self.hop_length).transpose(1, 2)

        # Autoregressive
        bits_energy_series = self.decoder(wave_mu_law, latents_upsampled)

        return bits_energy_series

    def generate(self, mel: Tensor) -> Tensor:
        """Generate waveform from mel-spectrogram.

        Input has variable length, and long zero padding is not good for RNN, so batch_size must be 1.

        Args:
            mel (Tensor(1, T_mel, freq)): Mel-spectrogram tensor. 
        Returns:
            (Tensor(1, T_mel * hop_length)) Generated waveform. A sample point is in range [-1, 1].
        """

        # Encoding for conditioning
        latents, _ = self.encoder(mel)

        # Cond. Upsampling
        latents_upsampled: Tensor = F.interpolate(latents.transpose(1, 2), scale_factor=self.hop_length).transpose(1, 2)

        # Autoregressive
        output_mu_law = self.decoder.generate(latents_upsampled)

        # μ-law expansion.
        # range: [0, 2^bit -1] => [-1, 1]
        # [PyTorch](https://pytorch.org/audio/stable/transforms.html#mulawdecoding)
        # bshall/UniversalVocoding use librosa, so range adaption ([0, n] -> [-n/2, n/2]) was needed.
        output_wave: Tensor = self.mulaw_dec(output_mu_law)

        return output_wave