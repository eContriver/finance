starting Ideas on how to do these indicators

ATR
#

declare lower;

input length = 14;
input averageType = AverageType.WILDERS;

plot ATR = MovingAverage(averageType, TrueRange(high, close, low), length);
ATR.SetDefaultColor(GetColor(8));

-WHAT IS WILDERS AVERAGING TYPE
	- wilders is an EMA (exponential moving average), that also gets multiplied by 1/length
	- SUPERTREND USES HULL AVERAGE TYPE
	- BUT IT ALSO ENDS UP CALLING THE TrueRange FUNCTION.  NEED TO FIND THAT
-WHAT IS THE TRUERANGE FUNCTION
Returns the true range (TR).



TR is the greatest of the following:

-   the difference between the current high and the current low
-   the difference between the current high and the previous close
-   the difference between the previous close and the current low
- By default, the average true range is a 14-period Wilder's moving average of this value; both the period and the type of moving average can be customized using the study input parameters.
SO WHATEVER LENGTH VALUE YOU GIVE IT, THEY DO A "TRUE RANGE" CALCULATION FOR EACH "DAY", THEN THEY DO A "WILDERS" SMOOTHING ACROSS ALL OF THEM (ASSUMING THOSE ARE THE DEFAULT VALUES)




EMA, exponential moving average
~~https://sciencing.com/calculate-moving-range-4963173.html
- ~~the first calculation is an SMA
- ~~everything after that is an EMA term
	- ~~EMA=(closing price − previous day’s EMA)× smoothing constant as a decimal + previous day’s EMA
- ~~to be perfectly accurate, EMA's should be started being calculated at "time=0".  for us, this means:
	- ~~EMA should always be fed the current saved, old EMA calculations list
	- ~~EMA will now calculate the newest EMA term and return it
	- ~~the strategy SHOULD put the newest EMA term at [0], and pop off the last term if the list is too long~~
i think that is officially correct, but it's not the version i want to replicate
The formula for the calculation of the exponential moving average is recursively defined as follows:

`EMA1 = price1;`
`EMA2 = α*price2 + (1 - α)*EMA1;`
`EMA3 = α*price3 + (1 - α)*EMA2;`
`EMAN = α*priceN + (1 - α)*EMAN-1;`

where α is a smoothing coefficient equal to `2/(length + 1)`.

> The key difference between a simple moving average (SMA) and the exponential moving average (EMA) is that in the EMA calculation, the most recent data is weighted to have more of an impact. That makes EMAs quicker than SMAs to adjust and reflect trends. On the downside, an EMA requires a lot more data to be reasonably accurate.

so price1 in the above example, is the most recent price that exists




WMA, weighted moving average
WMA = (P1 * 5) + (P2 * 4) + (P3 * 3) + (P4 * 2) + (P5 * 1) / (5 + 4+ 3 + 2 + 1)

Where:  
P1 = current price  
P2 = price one bar ago, etc…






Averaging type, HULL
(needs WMA, weighted moving average)

The formula for the Hull Moving Average uses two different weighted moving averages (WMAs) of price, plus a third WMA to smooth the raw moving average. There are three parts to the calculation. In the formulas listed below, “n” indicates the number of periods specified by the chartist.

First, calculate two WMAs: one with the specified number of periods and one with half the specified number of periods.

WMA1 = WMA(n/2) of price
WMA2 = WMA(n) of price

Second, calculate the raw (non-smoothed) Hull Moving Average.

Raw HMA = (2 * WMA1) - WMA2

Third, smooth the raw HMA with another WMA, this one with the square root of the specified number of periods.

HMA = WMA(Raw HMA, sqrt(n))


OK, IT WAS CONFUSING AT FIRST, BUT I THINK I UNDERSTAND IT.
1. EACH OF THE EARLIER WMA STEPS, SHOULD ACTUALLY BE RETURNING A LIST OF WMA VALUES.  WHY?  BECAUSE THE LAST WMA CALCULATION WE SEE, DOES STILL NEED A LIST OF DATA TO DO A REAL WMA CALCULATION WITH.
2. BUT IF THAT'S TRUE, WHAT IS THE HMA VALUE THAT WE WILL USE AT THE END?  EASY.  EVEN THOUGH THE LAST WMA WILL STILL RESULT IN A LIST OF VALUES THAT HMA WILL HAVE, THE 0TH ELEMEHT, THE [0] POSITION OF HMA, IS THE ONE WE WANT.
3. SO THEN THE THINGS IN THE RAW HMA CALCULATION, IS A SUBTRACTION FOR EACH CORRESPONDING ELEMENTS IN THE WMA1 AND WMA2 ARRAY THAT MATCH UP. BUT WMA1 AND WMA2 WILL NOT BE THE SAME LENGTH, SO WE WILL JUST DISCARD SOME OF THE EXTRA VALUES
4. SO GOING BACK TO THE START, WE WILL CALCULATE A WMA, STARTING AT POSITION 0 OF THE PRICE LIST WE START WITH.  THEN WE GOT TO PRICES[1], DO ANOTHER WMA, AND THAT IS WMA[1] IN EACH LIST, ETC UNTIL WE GET TO THE END OF OUR LOCAL PRICE LIST AND CANNOT COMPLETE ANOTHER FULL WMA





LinDev, LinearDeviation
> Linear deviation measures the average absolute difference between the mean and the current value.
def linDev = LinDev(price, lengthCCI);
- find the mean, given a length of time
	- closing prices
- find the absolute difference between the current closing price and that







RSI
#

declare lower;

input length = 14;
input over_Bought = 70;
input over_Sold = 30;
input price = close;
input averageType = AverageType.WILDERS;
input showBreakoutSignals = no;

def NetChgAvg = MovingAverage(averageType, price - price[1], length);
def TotChgAvg = MovingAverage(averageType, AbsValue(price - price[1]), length);
def ChgRatio = if TotChgAvg != 0 then NetChgAvg / TotChgAvg else 0;

plot RSI = 50 * (ChgRatio + 1);
plot OverSold = over_Sold;
plot OverBought = over_Bought;
plot UpSignal = if RSI crosses above OverSold then OverSold else Double.NaN;
plot DownSignal = if RSI crosses below OverBought then OverBought else Double.NaN;

UpSignal.SetHiding(!showBreakoutSignals);
DownSignal.SetHiding(!showBreakoutSignals);

RSI.DefineColor("OverBought", GetColor(5));
RSI.DefineColor("Normal", GetColor(7));
RSI.DefineColor("OverSold", GetColor(1));
RSI.AssignValueColor(if RSI > over_Bought then RSI.color("OverBought") else if RSI < over_Sold then RSI.color("OverSold") else RSI.color("Normal"));
OverSold.SetDefaultColor(GetColor(8));
OverBought.SetDefaultColor(GetColor(8));
UpSignal.SetDefaultColor(Color.UPTICK);
UpSignal.SetPaintingStrategy(PaintingStrategy.ARROW_UP);
DownSignal.SetDefaultColor(Color.DOWNTICK);
DownSignal.SetPaintingStrategy(PaintingStrategy.ARROW_DOWN);








SchaffTrendCycle
#

declare lower;

input fastLength = 23;
input slowLength = 50;
input KPeriod = 10;
input DPeriod = 3;
input over_bought = 75;
input over_sold = 25;
input averageType = AverageType.EXPONENTIAL;

def macd = MovingAverage(averageType, close, fastLength) - MovingAverage(averageType, close, slowLength);
def fastK1 = FastKCustom(macd, KPeriod);
def fastD1 = MovingAverage(averageType, fastK1, DPeriod);
def fastK2 = FastKCustom(fastD1, KPeriod);
plot STC = MovingAverage(averageType, fastK2, DPeriod);
plot OverBought = over_bought;
plot OverSold = over_sold;

STC.SetDefaultColor(GetColor(8));
OverBought.SetDefaultColor(GetColor(7));
OverSold.SetDefaultColor(GetColor(7));











MACD

#

declare lower;

input fastLength = 12;
input slowLength = 26;
input MACDLength = 9;
input averageType = AverageType.EXPONENTIAL;
input showBreakoutSignals = no;

plot Value = MovingAverage(averageType, close, fastLength) - MovingAverage(averageType, close, slowLength);
plot Avg = MovingAverage(averageType, Value, MACDLength);

plot Diff = Value - Avg;
plot ZeroLine = 0;

plot UpSignal = if Diff crosses above ZeroLine then ZeroLine else Double.NaN;
plot DownSignal = if Diff crosses below ZeroLine then ZeroLine else Double.NaN;

UpSignal.SetHiding(!showBreakoutSignals);
DownSignal.SetHiding(!showBreakoutSignals);

Value.SetDefaultColor(GetColor(1));
Avg.SetDefaultColor(GetColor(8));
Diff.SetDefaultColor(GetColor(5));
Diff.SetPaintingStrategy(PaintingStrategy.HISTOGRAM);
Diff.SetLineWeight(3);
Diff.DefineColor("Positive and Up", Color.GREEN);
Diff.DefineColor("Positive and Down", Color.DARK_GREEN);
Diff.DefineColor("Negative and Down", Color.RED);
Diff.DefineColor("Negative and Up", Color.DARK_RED);
Diff.AssignValueColor(if Diff >= 0 then if Diff > Diff[1] then Diff.color("Positive and Up") else Diff.color("Positive and Down") else if Diff < Diff[1] then Diff.color("Negative and Down") else Diff.color("Negative and Up"));
ZeroLine.SetDefaultColor(GetColor(0));
UpSignal.SetDefaultColor(Color.UPTICK);
UpSignal.SetPaintingStrategy(PaintingStrategy.ARROW_UP);
DownSignal.SetDefaultColor(Color.DOWNTICK);
DownSignal.SetPaintingStrategy(PaintingStrategy.ARROW_DOWN);


OH, SO THIS REQUIRES EMA LIST RESULTS JUST LIKE THE HULL AVERAGING DOES.  SO EMA WILL EITHER NEED TO RETURN THINGS IN A LIST, OR IT WILL NEED TO BE REPEATEDLY CALLED LIKE HMA CALLS WMA MANY TIMES.  






CMF
#

declare lower;
input length = 21;

def tmp_var = 
if high == low then 
  volume 
else 
  (close - low - (high - close)) / (high - low) * volume
;

def sum_close = sum(tmp_var, length);
def total = sum(volume, length);

plot CMF = 
if total == 0 then 
  0 
else 
  sum_close / total
;
CMF.SetDefaultColor(GetColor(1));

plot ZeroLine = 0;
ZeroLine.SetDefaultColor(GetColor(5));











SuperTREND

# SuperTrend CCI ATR Trend
# tomsk
# 11.18.2019

# V1.0 - 08.10.2019 - dtek  - Initial release of SuperTrend CCI ATR Trend
# V2.0 - 11.18.2019 - tomsk - Modified the logic, cleaned up code for consistency

# SUPERTREND BY MOBIUS AND CCI ATR TREND COMBINED INTO ONE CHART INDICATOR,
# BOTH IN AGREEMENT IS A VERY POWERFUL SIGNAL IF TRENDING. VERY GOOD AT CATCHING
# REVERSALS. WORKS WELL ON 1 AND 5 MIN CHARTS. PLOT IS THE COMBINATION LOWEST
# FOR UPTREND AND HIGHEST OF THE DOWNTREND. DOTS COLORED IF BOTH IN AGREEMENT
# OR GREY IF NOT -  08/10/2019 DTEK

# Supertrend, extracted from Mobius original code

input ST_Atr_Mult = 1.0;    # was .70
input ST_nATR = 4;
input ST_AvgType = AverageType.HULL;
input ShowLabel = yes;
def c = close;
def v = volume;

def ATR = MovingAverage(ST_AvgType, TrueRange(high, close, low), ST_nATR);
def UP = HL2 + (ST_Atr_Mult* ATR);
def DN = HL2 + (-ST_Atr_Mult * ATR);
def ST = if close < ST[1] then UP else DN;

# CCI_ATR measures distance from the mean. Calculates a trend
# line based on that distance using ATR as the locator for the line.
# Credit goes to Mobius for the underlying logic

input lengthCCI = 50;      # Was 20
input lengthATR = 21;      # Was 4
input AtrFactor = 1.0;     # Was 0.7

def ATRCCI = Average(TrueRange(high, close, low), lengthATR) * AtrFactor;
def price = close + low + high;
def linDev = LinDev(price, lengthCCI);
def CCI = if linDev == 0
          then 0
          else (price - Average(price, lengthCCI)) / linDev / 0.015;

def MT1 = if CCI > 0
          then Max(MT1[1], HL2 - ATRCCI)
          else Min(MT1[1], HL2 + ATRCCI);

# Alignment of Supertrend and CCI ATR indicators

def Pos_State = close > ST and close > MT1;
def Neg_State = close < ST and close < MT1;

# Combined Signal Approach - Supertrend and ATR CCI

plot CSA = MT1;
CSA.AssignValueColor(if Pos_State then Color.CYAN
                     else if Neg_State then Color.MAGENTA
                     else Color.YELLOW);

# Buy/Sell Signals using state transitions

def BuySignal = (!Pos_State[1] and Pos_State);
def SellSignal = !Neg_State[1] and Neg_State;

# Buy/Sell Arrows

plot BuySignalArrow = if BuySignal then 0.995 * MT1 else Double.NaN;
BuySignalArrow.SetPaintingStrategy(PaintingStrategy.ARROW_UP);
BuySignalArrow.SetDefaultColor(Color.CYAN);
BuySignalArrow.SetLineWeight(5);

plot SellSignalArrow = if SellSignal then 1.005 * MT1 else Double.NaN;
SellSignalArrow.SetPaintingStrategy(PaintingStrategy.ARROW_DOWN);
SellSignalArrow.SetDefaultColor(Color.PINK);
SellSignalArrow.SetLineWeight(5);

# Candle Colors

AssignPriceColor(if Pos_State then Color.GREEN
                 else if Neg_State then Color.RED
                 else Color.YELLOW);
# End SuperTrend CCI ATR Trend
def upBars = if c < ST
             then upBars[1] + 1
             else upBars[1];
def upCycles = if c < ST and c[1] > ST[1]
               then upCycles[1] + 1
               else upCycles[1];

def dnBars = if c > ST
             then dnBars[1] + 1
             else dnBars[1];
def dnCycles = if c > ST and c[1] < ST[1]
               then dnCycles[1] + 1
               else dnCycles[1];
def upCycleCount = upBars / upCycles;
def dnCycleCount = dnBars / dnCycles;

def thisCycle = if c < ST and c[1] > ST[1]
                then 1
                else if c < ST
                then thisCycle[1] + 1
                else if c > ST and c[1] < ST[1]
                     then 1
                     else if c > ST
                          then thisCycle[1] + 1
                          else thisCycle[1];
def Volup = (fold i = 0 to thisCycle
             do if i > 0
                then Volup[1] + v
                else Volup[1]) / thisCycle;
DefineGlobalColor("LabelRed",  CreateColor(225, 0, 0)) ;
DefineGlobalColor("LabelGreen",  CreateColor(0, 165, 0)) ;
AddLabel(ShowLabel, "Up Bars = " + upBars + "; " +
                  "  Up Cycles = " + upCycles + "; " +
                  "  Dn Bars = " + dnBars + "; " +
                  "  Dn Cycles = " + dnCycles + "; " ,
if c < ST then GlobalColor("LabelRed") else GlobalColor("LabelGreen") );   #.... This portion of code modofies by jhf
AddLabel(ShowLabel,
                  "  Avg Up Cycle Count = " + Round(upCycleCount, 0) +
                  "  Avg Dn Cycle Count = " + Round(dnCycleCount, 0) +
                  "  This Cycle = " + thisCycle,
if c < ST then GlobalColor("LabelRed") else GlobalColor("LabelGreen") );   #.... This portion of code modofies by jhf
# End Code SuperTrend