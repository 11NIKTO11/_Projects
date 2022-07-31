import csv
import matplotlib.pyplot as plt
import pandas as pd
import datetime
import functools
import numpy as np
from sklearn.decomposition import PCA
import seaborn as sn
from varname import nameof

MAIN_TANKS = ["Orisa", "Reinhardt", "Winston","Wrecking Ball"]
OFF_TANKS = ["D.Va", "Zarya", "Roadhog","Sigma"]
TANKS = MAIN_TANKS +OFF_TANKS

MAIN_SUPP = ["Mercy", "Lucio", "Brigitte","Baptiste"]
FLEX_SUPP = ["Zenyatta", "Ana", "Moira"]
SUPP = MAIN_SUPP +FLEX_SUPP

PINPOINT = ["Ashe","McCree","Widowmaker"]
RANGED_HIT_SCAN = ["Ashe","McCree","Widowmaker","Soldier: 76", "Bastion"]
MELEE_HIT_SCAN = ["Tracer","Reaper","Sombra"]
HIT_SCAN = RANGED_HIT_SCAN + MELEE_HIT_SCAN
PROJECTILE = ["Echo", "Genji", "Hanzo", "Junkrat", "Mei", "Pharah"]
OTHER = ["Doomfist", "Symmetra", "Torbjörn"]

DPS = HIT_SCAN +PROJECTILE+OTHER

HEROES =TANKS+DPS+SUPP

CONTROL =['Busan','Ilios','Lijiang Tower','Nepal','Oasis']
ASSAULT =['Hanamura','Horizon Lunar Colony','Paris','Temple of Anubis','Volskaya Industries']
ESCORT =['Dorado','Havana','Junkertown','Rialto','Route 66','Watchpoint: Gibraltar']
HYBRID = ['Blizzard World','Eichenwalde','Hollywood',"King's Row",'Numbani']

PAYLOAD = "Push Payload"
POINT = "Capture Point"

DORADO = [85.7,96.2,85.8]
WATCHPOINT =[86,82.2,88.6]
def readFromCsv(filename):
    return pd.read_csv(filename, sep = ',')

def multi_bar(df,columns,c_labl,title,ylabel=""):
    labels = df.index.values.tolist()

    x = np.arange(len(labels))  # the label locations
    w_t = 0.8  # the width of the bars
    w = w_t/len(columns)
    fig, ax = plt.subplots()
    rects=[]
    off = w/2
    for c,l in zip(columns,c_labl):
        rect = ax.bar(x - w_t/2 + off, df[c], w, label=l)
        rects.append(rect)
        off = off+w

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_xticks(x)
    ax.tick_params(axis='x',rotation=45)
    ax.set_xticklabels(labels)
    ax.legend()
    for r in rects:
        ax.bar_label(r, padding=3)
    fig.tight_layout()
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    plt.show()

def statPerTimePlayed(df,statname):
    stat =df[df.stat_name==statname].stat_amount.sum()
    time =df[df.stat_name=='Time Played'].stat_amount.sum()

    return pd.Series(
        {
            'time':time,
            statname:stat*time
        }
    )

def Mouse2(df,st,heroes,statname,title=""):
    wa = df[df.hero_name.isin(heroes)]
    wa.set_index('player_name',drop=False)
    func = functools.partial(statPerTimePlayed,statname=statname)
    wa = wa.groupby(['player_name','map_name','esports_match_id','hero_name'],as_index=False).apply(func)
    wa = wa.set_index('player_name').join(st.set_index('Player'),how='inner')
    wa = wa.groupby("MouseModel").agg({statname:'sum','time':'sum'})
    wa[statname] = wa[statname].div(wa['time'])
    wa['time'] = wa['time'].div(wa['time'].sum())
    multi_bar(wa.round(3),[statname,'time'],['Accuracy','Relevance'],title+ ' - ' + statname)

def Sensitivity2(df,st,heroes,statname,title=""):
    wa = df[df.hero_name.isin(heroes)]
    wa.set_index('player_name',drop=False)
    func = functools.partial(statPerTimePlayed,statname=statname)
    wa = wa.groupby(['player_name','map_name','esports_match_id','hero_name'],as_index=False).apply(func)
    wa = wa.set_index('player_name').join(st.set_index('Player'),how='inner')
    wa = wa.groupby("cmPer360").agg({statname:'sum','time':'sum'})
    wa[statname] = wa[statname].div(wa['time'])
    wa['time'] = wa['time'].div(wa['time'].max())
    plt.scatter(wa.index.values.tolist(),wa[statname],marker='.',s=wa['time'].mul(1000))
    plt.xlabel("Distance to make 360 in cm")
    plt.ylabel(statname)
    plt.title(title+ ' - ' + statname)
    plt.show()

def Mouse(df,st,heroes,statname,title=""):
    wa = df[(df.hero_name.isin(heroes))&(df.stat_name==statname)]
    wa = wa.set_index('player_name').join(st.set_index('Player'),how='inner')
    wa = wa[["MouseModel","stat_amount"]]
    wa = wa.groupby("MouseModel").agg(['mean', 'count'])
    wa['stat_amount', 'count'] = wa['stat_amount', 'count'].divide(wa['stat_amount', 'count'].sum())
    multi_bar(wa,[('stat_amount', 'mean'),('stat_amount', 'count')],['accuracy','representation'],title+ ' - ' + statname)

def Sensitivity(df,st,heroes,statname,title=""):
    wa = df[(df.hero_name.isin(heroes))&(df.stat_name==statname)]
    wa = wa[["player_name","stat_amount"]]
    wa = wa.groupby("player_name").agg('mean')
    wa = wa.join(st.set_index('Player'),how='inner')
    wa = wa[["cmPer360","stat_amount"]]
    plt.scatter(wa["cmPer360"],wa["stat_amount"],marker='.')
    plt.title(title+ ' - ' + statname)
    plt.show()

#dmage ability vs weapon

def GearvsStats():
    df211 = readFromCsv('phs_2021_1.csv')
    df201 = readFromCsv('phs_2020_1.csv')
    df202 = readFromCsv('phs_2020_2.csv')
    df = pd.concat([df201,df202,df211])
    st = readFromCsv('player_settings.csv')
    heroes_groups =[RANGED_HIT_SCAN,HIT_SCAN,DPS]
    group_names = ["Ranged hit scan heroes",'Hit scan','Dps heroes']
    # for h,n in zip(heroes_groups,group_names):
    #     Mouse2(df,st,h,'Weapon Accuracy',title=n)
    #     Sensitivity2(df,st,h,'Weapon Accuracy',title=n)
    #     Mouse2(df,st,h,'Critical Hit Accuracy',title=n)
    #     Sensitivity2(df,st,h,'Critical Hit Accuracy',title=n)

    Sensitivity2(df,st,["Widowmaker"],'Scoped Critical Hit Accuracy',title = "Widowmaker")
    Sensitivity2(df,st,["Widowmaker"],'Scoped Accuracy',title = "Widowmaker")

def distance(df,checkpointDist):
    round = df.map_round.max()
    dist_a = df[df.map_round==round]["attacker_payload_distance"].tolist()[0]
    dist_d = df[df.map_round==round]["defender_payload_distance"].tolist()[0]
    round_a = df[df.map_round==round]["attacker_round_end_score"].tolist()[0]
    round_d = df[df.map_round==round]["defender_round_end_score"].tolist()[0]

    if( round_a>round_d):
        round_a =(round_a-1) 
    else:
        round_d = (df[df.map_round==(round-1)]["attacker_round_end_score"].tolist()[0])

    for i in range(round_a%3):
        dist_a = dist_a + checkpointDist[i]
    
    for i in range(round_d%3):
        dist_d = dist_d + checkpointDist[i]

    return pd.DataFrame({"A":[dist_a],"D":[dist_d]})

def NormalizedMapDist(map_name,checkpointDist):
    mms = readFromCsv('match_map_stats.csv')
    dist_f = functools.partial(distance,checkpointDist=checkpointDist)
    dis = mms[mms.map_name==map_name].groupby("match_id").apply(dist_f)
    dis = dis.div(np.array(DORADO).sum())
    print(dis)
    print(dis.A.max(),dis.D.max())
    all_dis =pd.DataFrame()
    all_dis["dist"] = pd.concat([dis.A,dis.D])
    print(all_dis)
    all_dis.to_csv(map_name.replace(':','') + "_dist.csv",index=False)

# NormalizedMapDist("Dorado",DORADO)
# NormalizedMapDist("Watchpoint: Gibraltar",WATCHPOINT)

def HeroStatAnalysis(df):
    BASIC_DMG_TYPES =[
        'Damage - Weapon',
        'Damage - Weapon Primary',
        'Damage - Weapon Secondary',
        'Damage - Weapon Scoped',
        'Damage - Weapon Charged',
        'Damage - Weapon Sentry',
        'Damage - Weapon Pistol',
        'Damage - Hyperspheres',
        'Damage - Pistol',
        'Damage - Quick Melee'
    ]

    ULTIMATE_KILL_TYPES=[
        'Nano Boost Assists',
        'Bob Kills',
        'Amplification Matrix Assists',
        'Tank Kills',
        'Self-Destruct Kills',
        'Meteor Strike Kills',
        'Duplicate Kills',
        'Dragonblade Kills',
        'Dragonstrike Kills',
        'RIP-Tire Kills',
        'Deadeye Kills',
        'Blizzard Kills',
        'Coalescence Kills',
        'Supercharger Assists',
        'Barrage Kills',
        'Death Blossom Kills',
        'Earthshatter Kills',
        'Whole Hog Kills',
        'Gravitic Flux Kills',
        'Tactical Visor Kills',
        'Molten Core Kills',
        'Pulse Bomb Kills',
        'Primal Rage Kills',
        'Minefield Kills',
        'Graviton Surge Kills'
    ]

    basic_dmg = df[df.stat_name.isin(BASIC_DMG_TYPES)].stat_amount.sum()
    dmg = df[df.stat_name=='Hero Damage Done'].stat_amount.sum()

    time = df[df.stat_name=='Time Played'].stat_amount.sum()
    holding = df[df.stat_name=='Time Holding Ultimate']

    build = pd.merge(
        df[(df.stat_name=='Time Building Ultimate')],
        holding[['esports_match_id','player_name']],
        how='inner')
    ultimate_charged =pd.merge(
        df[(df.stat_name=='Ultimates Earned - Fractional')],
        holding[['esports_match_id','player_name']],
        how='inner').stat_amount.sum() 
    print(ultimate_charged)
    ultimate_used =df[df.stat_name=='Ultimates Used'].stat_amount.sum()
    kills = df[df.stat_name=='Eliminations'].stat_amount.sum()
    return pd.Series({
        "Damage": dmg/time,
        "Ability":(dmg-basic_dmg)/time,
        "Basic":basic_dmg/time,
        "Time Played":time,
        "Relative Time Alive":(df[df.stat_name=='Time Alive'].stat_amount.sum()/time),
        "Ultimate build time":(build.stat_amount.sum()/ultimate_charged),
        "Ultimate holding time":(holding.stat_amount.sum()/ultimate_used),
        "K/D":kills/df[df.stat_name=='Deaths'].stat_amount.sum(),
        "Final blows":df[df.stat_name=='Final Blows'].stat_amount.sum()/kills,
        "Ultimate kills":df[df.stat_name.isin(ULTIMATE_KILL_TYPES)].stat_amount.sum()/ultimate_used,
        "Damage Taken":(df[df.stat_name=='Damage Taken'].stat_amount.sum()/time),
        "Healing Received":(df[df.stat_name=="Healing Received"].stat_amount.sum()/time),
        "Healing Done":(df[df.stat_name=="Healing Done"].stat_amount.sum()/time),
        })

def Heroes():
    df211 = readFromCsv('phs_2021_1.csv')
    df201 = readFromCsv('phs_2020_1.csv')
    df202 = readFromCsv('phs_2020_2.csv')
    df = pd.concat([df201,df202,df211])
    df = df[df.hero_name.isin(HEROES)]
    #time alive /time played
    hs = df.groupby("hero_name").apply(HeroStatAnalysis)
    print(hs)
    plot_col = ["Time Played"]
    multi_bar(hs[plot_col].div(3600).round(2),plot_col,plot_col,"PlayTime","Hours")
    plot_col = ['Relative Time Alive']
    multi_bar(hs[plot_col].round(2),plot_col,plot_col,"Survival rate")
    plot_col = ["K/D"]
    multi_bar(hs[plot_col].round(2),plot_col,plot_col,"Kill death ratio","Ratio")
    plot_col = ["Final blows"]
    multi_bar(hs[plot_col].round(2),plot_col,plot_col,"Kill to Finall blows ratio","Ratio")
    plot_col = ["Damage","Basic","Ability"]
    multi_bar(hs[plot_col].round(2),plot_col,plot_col,"Damage source","Damage per second")
    plot_col =["Damage Taken","Healing Received","Healing Done"]
    multi_bar(hs[plot_col].round(2),plot_col,plot_col,"Health & Healing","Health change per second")
    plot_col = ["Ultimate build time","Ultimate holding time"]
    multi_bar(hs[plot_col].round(2),plot_col,plot_col,"Ultimate economy","Time in seconds")
    plot_col = ["Ultimate kills"]
    multi_bar(hs[plot_col].round(2),plot_col,plot_col,"Kills pre ultimate","Kills")

def getFinalScore(df):
    round = df.map_round.max()
    sec_round = df[df.map_round!=round].map_round.max()
    round_a = df[df.map_round==round]["attacker_round_end_score"].tolist()[0]
    round_d = df[df.map_round==round]["defender_round_end_score"].tolist()[0]

    if( round_a>round_d):
        round_a =(round_a-1) 
    else:
        round_d = (df[df.map_round==sec_round]["attacker_round_end_score"].tolist()[0])

    return pd.Series({'A':round_a,'D':round_d})

def decide(x):
    if((x.score%3)==0):
        return pd.Series({"result":POINT})
    else:
        return pd.Series({"result":PAYLOAD})

def Maps():
    mms = readFromCsv('match_map_stats.csv')
    con = mms[mms.map_name.isin(CONTROL)]
    #sn.set(style='ticks', context='talk')
    con['control_round_name'] ='-' + con['control_round_name']
    sn.stripplot(x=con[["map_name",'control_round_name']].sum(axis=1),
        y=con[['attacker_control_perecent','defender_control_perecent']].min(axis=1),
        size=3,
        jitter=0.3
    )
    #sn.stripplot(x="map_name",y='control_round_name',data=con)
    sn.despine()
    plt.tick_params(axis='x',rotation=45)
    plt.title("Control maps - loser control percentage")
    plt.ylabel('control percentage')
    plt.show()
    for map in HYBRID:
        hyb = mms[mms.map_name==map]
        hyb =hyb.groupby("match_id").apply(getFinalScore)
        hyb_score =pd.DataFrame()
        hyb_score["score"] = pd.concat([hyb.A,hyb.D])
        hyb_score = hyb_score.apply( decide,axis=1)
        pl = len(hyb_score[hyb_score.result==PAYLOAD])
        po = len(hyb_score[hyb_score.result==POINT])
        plt.pie([po,pl],labels=[POINT,PAYLOAD],autopct='%.2f')
        plt.title(map)
        plt.show()


# df211 = readFromCsv('phs_2021_1.csv')
# df201 = readFromCsv('phs_2020_1.csv')
# df202 = readFromCsv('phs_2020_2.csv')
# df = pd.concat([df201,df202,df211])

# for s in df.stat_name.unique().tolist():
#     print(s)

#Heroes()
#Maps()
GearvsStats()

