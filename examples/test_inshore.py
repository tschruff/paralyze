import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import inshore


context = inshore.get('water_resour_res', type='context')
sns.set_context(context)

X = np.arange(0, 50)
Y = np.sin(X)

plt.plot(X, Y)
plt.show()
