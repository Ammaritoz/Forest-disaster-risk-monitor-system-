import pandas as pd

def loadAndFix(csv):
    DataLog = pd.read_csv(csv) #read csv file 
    DataLog.columns = [c.strip() for c in DataLog.columns] #Remove empty columns to prevent referencing errors
    DataLog = DataLog.sort_values("Time (seconds)") #Sort dataset based on time
    DataLog = DataLog.set_index("Time (seconds)") #Set time column as the index so each row is identified by its timestamp
    DataLog = DataLog.ffill() #Forward fill missing values because the micro:bit logs each sensor separately
    DataLog = DataLog[~DataLog.index.duplicated(keep="last")] #Remove duplicate timestamps to prevent errors when accessing rows later
    DataLog = DataLog.dropna(subset=["soil moisture", "Temp", "Light" ]) #Remove any remaining rows that do not contain all required sensor values
    return DataLog

def scaling(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def values(data):
    data = data.copy()
    data["dryness"] = scaling(data["soil moisture"], 500, 1023, 100, 0)
    data["tempN"] = scaling(data["Temp"], 16, 35, 0, 100)
    data["lightN"] = scaling(data["Light"], 0, 255, 0, 100)

    for i in data.index:  #ensures that any values that a registered below 0 or above 100 get rounded up or down repectively 
        if data.loc[i, "dryness"] < 0:
            data.loc[i, "dryness"] = 0
        elif data.loc[i, "dryness"] > 100:
            data.loc[i, "dryness"] = 100
        
        if data.loc[i, "tempN"] < 0:
            data.loc[i, "tempN"] = 0
        elif data.loc[i, "tempN"] > 100:
            data.loc[i, "tempN"] = 100
        
        if data.loc[i, "lightN"] < 0:
            data.loc[i, "lightN"] = 0
        elif data.loc[i, "lightN"] > 100:
            data.loc[i, "lightN"] = 100
    
    return data 
    
def risks(data):
    data = data.copy()

    data["DroughtRisk"] = (data["dryness"] * 70 + data["tempN"] * 30) / 100
    data["FireRisk"] = (data["DroughtRisk"] * 50 + (data["tempN"] * 30 + data["lightN"] * 20)) / 100

    for i in data.index:  #ensures that any values that a registered below 0 or above 100 get rounded up or down repectively 
        if data.loc[i, "DroughtRisk"] < 0:
            data.loc[i, "DroughtRisk"] = 0
        elif data.loc[i, "DroughtRisk"] > 100:
            data.loc[i, "DroughtRisk"] = 100
        
        if data.loc[i, "FireRisk"] < 0:
            data.loc[i, "FireRisk"] = 0
        elif data.loc[i, "FireRisk"] > 100:
            data.loc[i, "FireRisk"] = 100

    return data

data = loadAndFix("microbit.csv")
# 1) Baseline
base = risks(values(data))
print("Base - Fire max:", round(float(base["FireRisk"].max()),2),"%")
print("Base - Fire avg:", round(float(base["FireRisk"].mean()),2),"%")
print("Base - Drought max:", round(float(base["DroughtRisk"].max()),2),"%")
print("Base - Drought avg:", round(float(base["DroughtRisk"].mean()),2),"%")

# 2) What if temperature increases
temp_up = data.copy()
temp_up["Temp"] = temp_up["Temp"] + 5  
temp_up = risks(values(temp_up))
print("Temp +5C - Fire max:", round(float(temp_up["FireRisk"].max()),2),"%")
print("Temp +5C - Fire avg:", round(float(temp_up["FireRisk"].mean()),2),"%")
print("Temp +5C - Drought max:", round(float(temp_up["DroughtRisk"].max()),2),"%")
print("Temp +5C - Drought avg:", round(float(temp_up["DroughtRisk"].mean()),2),"%")


# 3) What if soil moisture decreases (drier)
moist_down = data.copy()
moist_down["soil moisture"] = moist_down["soil moisture"] - 200  
moist_down = risks(values(moist_down))
print("Drier soil (raw -200) - Fire max:",  round(float(moist_down["FireRisk"].max()),2),"%")
print("Drier soil (raw -200) - Fire avg:", round(float(moist_down["FireRisk"].mean()),2),"%")
print("Drier soil (raw -200) - Drought max:", round(float(moist_down["DroughtRisk"].max()),2),"%")
print("Drier soil (raw -200) - Drought avg:", round(float(moist_down["DroughtRisk"].mean()),2),"%")

data = loadAndFix("microbit.csv")
data = values(data)
data = risks(data)

print(data[["DroughtRisk", "FireRisk"]])