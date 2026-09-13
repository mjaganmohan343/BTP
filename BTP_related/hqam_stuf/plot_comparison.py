import numpy as np
import matplotlib.pyplot as plt
from scipy.special import erfc

# 1. Define the Gaussian Q-function using the complementary error function
def Q(x):
    return 0.5 * erfc(x / np.sqrt(2))

# 2. Simulated Data Points
# Conventional Square 16-QAM Simulation Data (Corrected Coherent Simulation with Loop BW = 0.01)
ebn0_db_sim_16qam = np.array([0.00, 1.50, 3.00, 4.44, 6.02, 7.96, 8.87, 9.90, 11.06, 11.70, 12.39, 13.15, 13.98, 14.89, 15.92, 17.08, 18.42, 20.00])
ber_sim_16qam = np.array([1.420429e-01, 1.092967e-01, 7.835844e-02, 5.177411e-02, 2.822600e-02, 9.808934e-03, 5.050272e-03, 2.041047e-03, 5.636707e-04, 2.358999e-04, 7.956011e-05, 2.001504e-05, 3.300419e-06, 3.500445e-07, 1.250159e-08, 6.194351e-11, 3.327591e-14, 1.404037e-19])


# 16-HexQAM (H-QAM) Simulation Data
ebn0_db_sim_hqam = np.array([0.00, 1.50, 3.00, 4.44, 6.02, 7.96, 8.87, 9.90, 11.06, 11.70, 12.39, 13.15, 13.98, 14.89, 15.92, 17.08, 18.42, 20.00])
ber_sim_hqam = np.array([1.5200e-01, 1.1400e-01, 8.2100e-02, 6.0300e-02, 3.0500e-02, 9.5300e-03, 4.5400e-03, 1.6500e-03, 3.8700e-04, 1.4500e-04, 4.4100e-05, 1.0200e-05, 1.2400e-06, 8.2400e-08, 1.9800e-09, 8.4200e-12, 2.1100e-15, 2.1500e-21])

# 3. Generate smooth range for Theoretical Curves from 0 to 20 dB
ebn0_db_theo = np.linspace(0, 20, 600)
ebn0_lin_theo = 10**(ebn0_db_theo / 10)
esn0_lin_theo = 4 * ebn0_lin_theo  # For M=16, Es = 4 * Eb

# 4. Compute Exact Theoretical BER for Square 16-QAM with Gray Coding
ber_theo_16qam = (3/4)*Q(np.sqrt((4/5)*ebn0_lin_theo)) + (1/2)*Q(3*np.sqrt((4/5)*ebn0_lin_theo)) - (1/4)*Q(5*np.sqrt((4/5)*ebn0_lin_theo))

# 5. Compute Approximate Theoretical BER for 16-HexQAM (H-QAM) from the paper
M = 16
A = 4.125
B = 4.4948
kappa = 2 / 9  # Constellation factor for 16-HexQAM

P_s_hqam = A * Q(np.sqrt(kappa * esn0_lin_theo)) - B * Q(np.sqrt((10/11) * kappa * esn0_lin_theo)) * Q(np.sqrt((1/3) * kappa * esn0_lin_theo))
ber_theo_hqam = P_s_hqam / np.log2(M)

# Filter out zero BER values to prevent plotting artifacts / plunging lines on log scale
mask_16qam = ber_sim_16qam > 0
ebn0_db_sim_16qam = ebn0_db_sim_16qam[mask_16qam]
ber_sim_16qam = ber_sim_16qam[mask_16qam]

mask_hqam = ber_sim_hqam > 0
ebn0_db_sim_hqam = ebn0_db_sim_hqam[mask_hqam]
ber_sim_hqam = ber_sim_hqam[mask_hqam]

# 6. Plotting
fig, ax = plt.subplots(figsize=(12, 8), dpi=300)

# Colors matching the design choices
c_16qam_theo = '#2EC4B6'  # Emerald Green
c_16qam_sim = '#FF9F1C'   # Amber
c_hqam_theo = '#E71D36'   # Crimson
c_hqam_sim = '#011627'    # Royal Blue / Dark Blue

# Plot theoretical curves
ax.semilogy(ebn0_db_theo, ber_theo_16qam, color=c_16qam_theo, linestyle='-', linewidth=2.5, 
            label='Theoretical Closed-Form Curve (Square 16-QAM)')
ax.semilogy(ebn0_db_theo, ber_theo_hqam, color=c_hqam_theo, linestyle='-', linewidth=2.5, 
            label='Theoretical Closed-Form Curve (16-HexQAM)')

# Plot simulated curves
ax.semilogy(ebn0_db_sim_16qam, ber_sim_16qam, color=c_16qam_sim, marker='s', linestyle='--', linewidth=1.5, 
            markersize=6, markeredgewidth=1.2, label='Simulation Performance (Square 16-QAM)')
ax.semilogy(ebn0_db_sim_hqam, ber_sim_hqam, color=c_hqam_sim, marker='o', linestyle='--', linewidth=1.5, 
            markersize=6, markeredgewidth=1.2, label='Simulation Performance (16-HexQAM)')

# Format Plot
ax.grid(True, which="both", linestyle="--", alpha=0.5, color='#CBD5E1')
ax.minorticks_on()

# Customize font size and weights
ax.set_xlabel(r'$E_b/N_0$ (dB)', fontsize=12, fontweight='bold', labelpad=10)
ax.set_ylabel('Bit Error Rate (BER)', fontsize=12, fontweight='bold', labelpad=10)
ax.set_title(r'BER vs $E_b/N_0$ Comparison: Conventional 16-QAM vs. 16-HexQAM', fontsize=14, pad=18, fontweight='bold')

# Legend styling
ax.legend(fontsize=10.5, loc='upper right', frameon=True, shadow=True, facecolor='#F8FAFC', edgecolor='#E2E8F0')

# Axes limits
ax.set_xlim(0, 20)
ax.set_ylim(1e-10, 1)

# Save the figure
plt.tight_layout()
output_path = 'ber_comparison.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"Plot saved successfully as '{output_path}'.")
