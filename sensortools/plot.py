import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns


def searchDistPlot(df, var, sensor=None):
    """
    Create a Distribution plot of one variable. Optionally, subset by sensor
    """
    if sensor:
        df = df.loc[df.sensor == sensor]
    sns.distplot(df[var])


def searchVarPlot(df, var1=None, var2=None, sensor=None):
    """
    Create a Jointplot of two variables. Optionally, subset by sensor
    """
    if sensor:
        df = df[df.sensor == sensor]
    g = sns.jointplot(df[var1], df[var2], kind='kde')
    try:
        # seems to fail on GBDX Notebooks
        g.ax_joint.legend_.remove()
    except:
        pass


def searchSensorComparePlot(df, var1=None, var2=None):
    """
    Compare multiple sensors and variables
    """
    g = sns.FacetGrid(df, col="sensor")
    g.map(sns.kdeplot, var1, var2)


def searchBarPlot(df):
    """
    Bar Plot of the count of sensor images in search
    """
    f, ax = plt.subplots(figsize=(15,6))
    sns.countplot(x='sensor', data=df)
    ax.set_ylabel('Image Count')


def searchScatterPlot(df):
    """
    Function to plot out the results of an image/AOI search
    """

    f, ax = plt.subplots(figsize=(12,6))
    sns.despine(bottom=True, left=True)

    sns.stripplot(x="timestamp", y="sensor",
                  data=df, dodge=True, jitter=True,
                  alpha=.25, zorder=1, size=10)

    years = mdates.YearLocator()   # every year
    months = mdates.MonthLocator()  # every month
    yearsFmt = mdates.DateFormatter('%Y')
    monthsFmt = mdates.DateFormatter('%m')

    # TODO: check len of date range and adjust labels accordingly
    ax.xaxis.set_major_locator(years)
    ax.xaxis.set_major_formatter(yearsFmt)
    ax.xaxis.set_minor_locator(months)

    s = df.groupby(['sensor']).count()

    _ = ax.set_yticklabels(s.index + ' Count: ' + s.x.map(str))
    _ = ax.get_yaxis().set_visible(False)

    legend = ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.1), ncol=len(s.index))
    for t in legend.get_texts():
        c = s[s.index == t.get_text()].x.values[0]
        label = t.get_text() + ' Count:' + str(c)
        t.set_text(label)
