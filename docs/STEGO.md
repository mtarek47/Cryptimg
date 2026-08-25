# Stegstr Steganography Engine Specification

## 1. Overview
The Stegstr StegEngine implements a transformation-resistant steganographic transport layer designed to survive real-world social media media processing pipelines.

## 2. Mid-Frequency 2D-DCT Quantization Index Modulation (QIM)
- **Luminance Channel ($Y$)**: Image is converted from RGB to $YCbCr$ color space. Embedding operates exclusively on the Luminance ($Y$) channel to withstand $4:2:0$ chroma subsampling.
- **2D-DCT Block Decomposition**: The $Y$ channel is divided into non-overlapping $8 \times 8$ blocks. 2D Discrete Cosine Transform is computed for each block:
  $$D_{u,v} = \sum_{x=0}^7 \sum_{y=0}^7 Y(x,y) \alpha(u) \alpha(v) \cos\left(\frac{\pi(2x+1)u}{16}\right) \cos\left(\frac{\pi(2y+1)v}{16}\right)$$
- **Mid-Frequency Coefficient Selection**: Embeds payload bits into mid-frequency AC coefficients $(3,2), (2,3), (4,1), (1,4), (3,3), (2,4), (4,2), (3,4)$. These coefficients survive lossy JPEG quantization tables while remaining visually imperceptible.
- **QIM Modulated Step Size ($\Delta$)**:
  $$C'(u,v) = \text{round}\left(\frac{C(u,v) - b \cdot \Delta/2}{\Delta}\right) \cdot \Delta + b \cdot \Delta/2$$

## 3. Reed-Solomon Error Correction & Interleaving
- **Parity Redundancy**: Configurable parity levels: Fast (14%), Balanced (33%), Robust (60%), Maximum (100%).
- **Matrix Bit Interleaving**: Matrix permutation prevents contiguous burst errors caused by local image compression boundaries.
