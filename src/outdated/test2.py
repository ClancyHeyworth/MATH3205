import pandas as pd
from matplotlib import colormaps
import matplotlib.pyplot as plt

df = pd.read_csv('outputs/6.csv')

df = df.set_index('P')

df = df[['benders', 'mip']]



df.plot(kind='bar', colormap='tab10')
plt.yscale('log')
plt.ylabel('Time to Optimality (s)')
plt.xlabel('Proportion of Switches in Arcs')
plt.title('Computational Time of Benders and MIP on R6 Dataset')
plt.show()

print(df)