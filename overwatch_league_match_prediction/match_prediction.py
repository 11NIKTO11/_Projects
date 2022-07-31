
from logging import debug
from re import match
import pandas as pd
import numpy as np
from pandas.core.algorithms import unique 
import seaborn as sn
import matplotlib.pyplot as plt
import functools
from math import log2, sqrt
from scipy.stats import t
from pandas.api.types import CategoricalDtype
from sklearn import linear_model

from sklearn.neural_network import MLPClassifier
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import ElasticNetCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import KFold
from sklearn.metrics import classification_report,confusion_matrix
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_val_score
from sklearn import svm
from sklearn.utils import shuffle
#TODO REEVAUATE GRIDS
#TODO EVAL GRID ON IMPORTANT FEATURES
#TODO check index sorting in split_data to predict in time order
DEBUG=False
MAP_FILE= ["match_map_stats.csv"]
PLAYER_FILES = ["phs_2020_1.csv","phs_2020_2.csv","phs_2021_1.csv"]
TOURNAMENT ='OWL 2020 Regular Season'

MAIN_TANKS = ["Orisa", "Reinhardt", "Winston","Wrecking Ball"]
OFF_TANKS = ["D.Va", "Zarya", "Roadhog","Sigma"]
TANKS = MAIN_TANKS +OFF_TANKS
ROLE_TANK ='Tank'

MAIN_SUPP = ["Mercy", "Lúcio", "Brigitte","Baptiste"]
FLEX_SUPP = ["Zenyatta", "Ana", "Moira"]
SUPP = MAIN_SUPP +FLEX_SUPP
ROLE_SUPP='Supp'

PINPOINT = ["Ashe","McCree","Widowmaker"]
RANGED_HIT_SCAN = PINPOINT +["Soldier: 76", "Bastion"]
MELEE_HIT_SCAN = ["Tracer","Reaper","Sombra"]
HIT_SCAN = RANGED_HIT_SCAN + MELEE_HIT_SCAN
PROJECTILE = ["Echo", "Genji", "Hanzo", "Junkrat", "Mei", "Pharah"]
OTHER = ["Doomfist", "Symmetra", "Torbjörn"]
DPS = HIT_SCAN +PROJECTILE+OTHER
ROLE_DPS ='Dps'

HEROES =TANKS+DPS+SUPP
ROLES = [ROLE_TANK, ROLE_DPS, ROLE_SUPP]



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

MATCH_MAP_ID_COL = ["match_id", "game_number"]

RANDOM_STATE = 420
TEST_SIZE = 0.2
REGUL_FEATURES_COUNT = 100
SHUFFLE = True
SYMETRIC = False

#DATA PROCESING
def Read_from_csvs(filenames):
    return pd.concat([pd.read_csv(filename, sep = ',') for filename in filenames])

def Heroes_to_role(df,debug=False):
    heroes = set(df["hero_name"].unique())
    heroes.remove("All Heroes")

    if(heroes.issubset(set(TANKS))):
        return pd.Series({"role":ROLE_TANK})
    elif(heroes.issubset(set(DPS))):
        return pd.Series({"role":ROLE_DPS})
    elif(heroes.issubset(set(SUPP))):
        return pd.Series({"role":ROLE_SUPP})
    else:
        if debug:
            print("Role cannot be determined")
            print(heroes)
            print(df)
        return pd.Series({"role":"NULL"})

def Player_role(df,debug=False):
    tank_time = df[(df.stat_name=='Time Played') & (df.hero_name.isin(TANKS))].stat_amount.sum()
    dps_time = df[(df.stat_name=='Time Played') & (df.hero_name.isin(DPS))].stat_amount.sum()
    supp_time = df[(df.stat_name=='Time Played') & (df.hero_name.isin(SUPP))].stat_amount.sum()
    
    if debug:
        print('Played roles -',
            ' tank' if tank_time>0 else '',
            ' dps' if dps_time>0 else '',
            ' supp' if tank_time>0 else '')

    if (tank_time>dps_time) and (tank_time>supp_time):
        return pd.Series({"role":ROLE_TANK})
    elif dps_time>supp_time:
        return pd.Series({"role":ROLE_DPS})
    else:
        return pd.Series({"role":ROLE_SUPP})

def Get_players_by_matches_played(df_maps, df_players,debug =False):
    unique_maps = df_maps[["match_id", "game_number", "team_one_name", "team_two_name", "map_winner", "map_name"]].drop_duplicates()

    # #some err in role queue logs match - 34776  PAYLOAD  Route 66
    # unique_players = df_players[["esports_match_id", "map_type", "map_name","team_name","player_name","hero_name"]].drop_duplicates()
    # unique_players = unique_players.groupby(["esports_match_id", "map_type", "map_name","team_name","player_name"],as_index=False).apply(Heroes_to_role)
    # unique_players = unique_players[unique_players.Role=="NULL"][["esports_match_id", "map_type", "map_name"]]

    unique_players = df_players.groupby(["esports_match_id", "map_type", "map_name","team_name","player_name"],as_index=False).apply(Player_role)

    players_by_map = unique_maps.merge(unique_players, 
        how = "inner",
        left_on = ["match_id", "map_name"],
        right_on = ["esports_match_id", "map_name"]
        )

    players_by_map.drop("esports_match_id",axis=1,inplace =True)
    players_by_map.sort_values(["match_id","game_number","player_name"])
    players_by_map.reset_index(drop=True, inplace=True)

    if debug:
        print(unique_maps.head())
        print(unique_players.head())
        print(players_by_map.head(25))

    return players_by_map 

def Players_stats(df):
    #Player repres - 
    #   "Eliminations", "Deaths", "K/D",
    #   "Hero Damage Done", "Barrier Damage Done", "Damage Blocked", "Damage Taken", 
    #   "Healing Received", "Healing Done",
    #   "Shots Fired, "Final blows",
    #   "Time Played", "Objective Time", Objective Kills,
    #   "Ultimates Earned - Fractional", "Ultimate build time","Ultimate holding time","Ultimate kills"
    #   "Most Frequent Hero"

    time = df[df.stat_name=='Time Played'].stat_amount.sum()

    kills = df[df.stat_name=='Eliminations'].stat_amount.sum()
    deaths =df[df.stat_name=='Deaths'].stat_amount.sum()

    holding = df[df.stat_name=='Time Holding Ultimate']
    build = pd.merge(
        df[(df.stat_name=='Time Building Ultimate')],
        holding[['esports_match_id','hero_name']],
        how='inner')
    ultimate_charged =pd.merge(
        df[(df.stat_name=='Ultimates Earned - Fractional')],
        holding[['esports_match_id','hero_name']],
        how='inner').stat_amount.sum() 
 
    ultimate_used =df[df.stat_name=='Ultimates Used'].stat_amount.sum()
    return pd.Series({
        "Time Played":time,
        "Time Alive":(df[df.stat_name=='Time Alive'].stat_amount.sum()/time),
        "Objective Time":(df[df.stat_name=='Objective Time'].stat_amount.sum()/time),

        "Eliminations":kills/time,
        "Objective Kills":(df[df.stat_name=='Objective Kills'].stat_amount.sum()/time),
        "Final blows":df[df.stat_name=='Final Blows'].stat_amount.sum()/kills,
        "Deaths":deaths/time,
        "K/D":kills/deaths if deaths>0 else kills, #0? max? max vs kills?

        "Hero Damage Done": df[df.stat_name=='Hero Damage Done'].stat_amount.sum()/time,
        "Barrier Damage Done": df[df.stat_name=='Barrier Damage Done'].stat_amount.sum()/time,
        "Damage Blocked": df[df.stat_name=='Damage Blocked'].stat_amount.sum()/time, #only barrieir heroes?
        "Damage Taken":(df[df.stat_name=='Damage Taken'].stat_amount.sum()/time),
        "Healing Received":(df[df.stat_name=="Healing Received"].stat_amount.sum()/time),
        "Healing Done":(df[df.stat_name=="Healing Done"].stat_amount.sum()/time),


        "Ultimates Earned - Fractional":(df[df.stat_name=="Ultimates Earned - Fractional"].stat_amount.sum()/time),
        "Ultimate build time":(build.stat_amount.sum()/ultimate_charged),
        "Ultimate holding time":(holding.stat_amount.sum()/ultimate_used),
        "Ultimate kills":df[df.stat_name.isin(ULTIMATE_KILL_TYPES)].stat_amount.sum()/ultimate_used
        })
        #TODO heroes preference? 
        # represent by time? 
        # by relative player time?
        # by relative role played time?

# normalize = none, max, std 
# default = none
def Get_players_stats(df_players,normalize='none',debug=False):
    players_stats = df_players[df_players.hero_name.isin(HEROES)].groupby("player_name").apply(Players_stats)

    if normalize=='max':
        players_stats = players_stats/players_stats.max()
    elif normalize=='std':
        players_stats = (players_stats-players_stats.mean())/players_stats.std()

    if debug:
        print(players_stats)
    return players_stats

#DATA CODING
def Matches_to_numbers(players_by_map,debug=False):
    players_by_map_num = players_by_map[["match_id","game_number"]].copy()

    if debug:
        print(players_by_map)
        print(players_by_map_num.head())

    team_name_cats = CategoricalDtype(players_by_map["team_name"].unique())
    players_by_map_num["team_one"] = players_by_map["team_one_name"].astype(team_name_cats).cat.codes
    players_by_map_num["team_two"] = players_by_map["team_two_name"].astype(team_name_cats).cat.codes
    players_by_map_num["winner"] = players_by_map["map_winner"].astype(team_name_cats).cat.codes
    players_by_map_num["team"] = players_by_map["team_name"].astype(team_name_cats).cat.codes

    if debug:
        print(players_by_map_num.head())

    map_name_cats = CategoricalDtype(df_players["map_name"].unique())
    players_by_map_num["map"] = players_by_map['map_name'].astype(map_name_cats).cat.codes

    if debug:
        print(players_by_map_num.head())

    map_name_cats = CategoricalDtype(df_players["map_type"].unique())
    players_by_map_num["map_type"] = players_by_map['map_type'].astype(map_name_cats).cat.codes

    if debug:
        print(players_by_map_num.head())

    player_name_cats = CategoricalDtype(df_players["player_name"].unique())
    players_by_map_num["player"] = players_by_map['player_name'].astype(player_name_cats).cat.codes

    if debug:
        print(players_by_map_num)

    return players_by_map_num

def Maps_onehot(players_by_map,debug=False):
    maps= players_by_map[["match_id","game_number",'map_name','map_type']].drop_duplicates()
    maps= pd.get_dummies(maps,columns=['map_name','map_type']) 
    maps.set_index(["match_id","game_number"], inplace=True)
    if debug:
        print(maps.columns)
        print(maps)
    return maps

def Teams_and_results_onehot_minus(players_by_map,debug=False):
    teams_by_map = players_by_map[["match_id","game_number",'team_one_name','team_two_name', 'map_winner']].drop_duplicates()
    teams_by_map.set_index(["match_id","game_number"], inplace=True)
    #team one or team two does not contain some team- scikit LabelBinarizer
    teams_one_hot = pd.get_dummies(teams_by_map['team_one_name'])
    teams_two_hot = pd.get_dummies(teams_by_map['team_two_name'])*-1
    teams = teams_one_hot + teams_two_hot
    if debug:
        print(teams)

    teams_by_map['result'] = teams_by_map.apply(lambda row: 1 if row['team_one_name']==row['map_winner'] else -1, axis=1) 
    results = teams_by_map[['result']]
    if debug:
        print(results)

    return(results,teams)

def Players_onehot_minus(players_by_map,debug=False):
    players_one_hot = pd.get_dummies(players_by_map["player_name"])
    players_one_hot[players_by_map.team_name!=players_by_map.team_one_name]*=-1
    players_one_hot = players_one_hot.join(players_by_map[["match_id","game_number"]])
    players_one_hot = players_one_hot.groupby(["match_id","game_number"],as_index=False).sum()
    players_one_hot.set_index(["match_id","game_number"], inplace=True)
    if debug:
        print(players_one_hot)

    return players_one_hot

def Hot_one_input(players_by_map, symetrical=False, pos_neg_maps=False, debug=False):
    maps = Maps_onehot(players_by_map,debug=debug)
    results,teams = Teams_and_results_onehot_minus(players_by_map,debug=debug)
    players = Players_onehot_minus(players_by_map,debug=debug)
    input = results.join(teams).join(players)

    if symetrical:
        input= pd.concat([input,input*-1])
        if(debug):
            print(input)

    if pos_neg_maps:
        maps= maps.join(maps*-1,rsuffix='_minus')
        if(debug):
            print(maps)

    input = input.join(maps)

    if(debug):
        print(input.info())
        print(input.columns)
        print(input)

    return input

def Role_players_variations(team_players,role,player_stats,debug=False):
    role_players = pd.DataFrame()
    role_players[role] = team_players[team_players.role==role]["player_name"]
    role_players_variations = role_players.merge(role_players,how='cross', suffixes=('_1', '_2')) #drop same better way
    role_players_variations = role_players_variations[role_players_variations[role+'_1'] != role_players_variations[role+'_2']]
    if debug:
        print(role_players_variations)

    role_col=role_players_variations.columns
    for col in role_col:
        role_players_variations = role_players_variations.merge(player_stats.add_suffix('_'+col),how='inner',left_on=col,right_index=True)
    if debug:
        print(role_players_variations)
    
    role_players_variations= role_players_variations.drop(role_col,axis=1)
    if debug:
        print(role_players_variations)
        print(role_players_variations.columns)
    return role_players_variations

def Team_players_variations(team_players,player_stats,debug=False):
    if debug:
        print(team_players)

    rolecount = team_players['role'].value_counts()
    if debug:
        print(rolecount)

    if (rolecount!=2).all():
        print('Match roles are invalid')
        print(team_players)
        return pd.Series()

    team_roster = Role_players_variations(team_players,ROLE_TANK,player_stats,debug=debug).merge(
        Role_players_variations(team_players,ROLE_DPS,player_stats,debug=debug),how='cross', suffixes=('', '')).merge(
        Role_players_variations(team_players,ROLE_SUPP,player_stats,debug=debug),how='cross', suffixes=('', ''))

    if debug:
        print(team_roster)
    return team_roster

def Player_stats_input(players_by_map,player_stats,debug=False):
    maps = Maps_onehot(players_by_map,debug)
    results,teams = Teams_and_results_onehot_minus(players_by_map,debug=debug)
    teams_one = teams.replace(-1,0)
    teams_two = (teams*-1).replace(-1,0)
    if debug:
        print(teams_one)
        print(teams_two)
    represent_players = functools.partial(Team_players_variations,player_stats=player_stats,debug=False)
    team_one_players = players_by_map[players_by_map.team_name==players_by_map.team_one_name].groupby(["match_id","game_number"]).apply(represent_players).droplevel(2)
    team_two_players = players_by_map[players_by_map.team_name==players_by_map.team_two_name].groupby(["match_id","game_number"]).apply(represent_players).droplevel(2)
    if debug:
        print(team_one_players)
        print(team_two_players)
    
    teams_one = teams_one.join(team_one_players)
    teams_two = teams_two.join(team_two_players)

    input = results.join(maps).join(teams_one.add_suffix('_team_one')).join(teams_two.add_suffix('_team_two'))
    input_rev =(results*-1).join(maps).join(teams_two.add_suffix('_team_one')).join(teams_one.add_suffix('_team_two'))
    return pd.concat([input,input_rev])
    
#CLASSIFICATION
def calc_win_freq(row, train_data):
    TEAM_1 = row["team_one_name"]
    TEAM_2 = row["team_two_name"]
    all_matches = train_data[((train_data.team_one_name == TEAM_1) & (train_data.team_two_name == TEAM_2)) | ((train_data.team_one_name == TEAM_2) & (train_data.team_two_name == TEAM_1))]
    won_matches_t1 = all_matches[all_matches.map_winner == TEAM_1]
    winrate_t1 = np.random.uniform(0,1)
    if len(all_matches) > 0:
        winrate_t1 = len(won_matches_t1) / len(all_matches)
    if (winrate_t1 > 0.5):
        return TEAM_1
    else:
        return TEAM_2
   
class MFClassifier:

    def __init__(self) -> None:
        pass
    def fit(self,train_X, train_Y):
        self.teams = pd.unique(train_X.values.ravel())

        pass

    def score(self,test_X, test_Y):
        pass

def PlayerMLPClassifierGrid(X_train, y_train, X_test, y_test):
    print("--------------MLP GRID ---------------")
    params = {'activation': ['tanh'],
          'hidden_layer_sizes': [(4,), (3,), (5,)],
          'solver': ['sgd', 'adam'],
          'learning_rate' : ['constant', 'adaptive'],
          'max_iter': [2000, 1500],  
         }
    mlp_classif_grid = GridSearchCV(MLPClassifier(random_state=RANDOM_STATE), param_grid=params, n_jobs=-1, cv=8, verbose=5)
    mlp_classif_grid.fit(X_train,y_train)
    print('Train Accuracy : %.3f'%mlp_classif_grid.best_estimator_.score(X_train, y_train))
    print('Test Accuracy : %.3f'%mlp_classif_grid.best_estimator_.score(X_test, y_test))
    print('Best Accuracy Through Grid Search : %.3f'%mlp_classif_grid.best_score_)
    print('Best Parameters : ',mlp_classif_grid.best_params_)
    print(mlp_classif_grid.best_estimator_)

def TrivialMFClassifier(train_X, train_Y, test_X, test_Y):
    print("------------ MF Classifier ---------------")
    FOLD_COUNT = 8
    train_data = train_X[["team_one_name", "team_two_name"]]
    train_data["map_winner"] = train_Y
    test_data = test_X[["team_one_name", "team_two_name"]]
    test_data["map_winner"] = test_Y
    #data_freq = train_data.groupby(["team_one_name", "team_two_name", "map_winner"]).size()
    train_data.reset_index(drop = True)
    test_data.reset_index(drop = True)
    kf = KFold(n_splits= FOLD_COUNT, shuffle= True)
    accuracies = list([])
    for train_index, test_index in kf.split(train_data):
        X_train_fold= train_data.iloc[train_index, :]
        X_test_fold = train_data.iloc[test_index, :]
        calc_win_fixed = functools.partial(calc_win_freq, train_data = X_train_fold)
        X_test_fold["predicted_winner"] = X_test_fold.apply(calc_win_fixed, axis = 1) 
        predicted_bin = list(X_test_fold.apply(lambda row : 0 if row["predicted_winner"] == row["team_one_name"] else 1, axis = 1))
        true_bin = list(X_test_fold.apply(lambda row : 0 if row["map_winner"] == row["team_one_name"] else 1, axis = 1))
        accuracy = sum([abs(abs(predicted_bin[index] - true_bin[index]) - 1) for index in range(len(predicted_bin))]) / len(predicted_bin)
        accuracies.append(accuracy)
    ConfidenceInterval(pd.Series(accuracies))
    calc_win_fixed = functools.partial(calc_win_freq, train_data = train_data)
    test_data["predicted_winner"] = test_data.apply(calc_win_fixed, axis = 1)
    predicted_bin = list(test_data.apply(lambda row : 1 if row["predicted_winner"] == row["team_two_name"] else -1 if row["predicted_winner"] == row["team_one_name"] else  0, axis = 1))
    true_bin = list(test_data.apply(lambda row : 1 if row["map_winner"] == row["team_two_name"] else -1 if row["map_winner"] == row["team_one_name"] else  0, axis = 1))
    accuracy = sum([1 if true_bin[index] == predicted_bin[index] else 0 for index in range(len(predicted_bin))])
    print(f"Test accuracy: { accuracy / len(predicted_bin)}")
    cf_test_matrix = confusion_matrix(test_Y, test_data["predicted_winner"], normalize= "true")
    
    ax= plt.subplot()
    plt.figure(figsize=(5,3))
    sn.heatmap(cf_test_matrix, annot=True, ax = ax)
    #plt.title('Confusion matrix for test data')
    #plt.xlabel('Predicted')
    #plt.ylabel('Actual')
    ax.set_xlabel('Predicted labels')
    ax.set_ylabel('True labels') 
    ax.set_title('Confusion Matrix') 
    team_labels = list(set((list(test_data["predicted_winner"]) + list(test_Y))))
    print("TEAM LABELS")
    print(team_labels)
    ax.xaxis.set_ticklabels(team_labels)
    ax.yaxis.set_ticklabels(team_labels)
    plt.show()

    cf_binary_matrix = confusion_matrix(true_bin, predicted_bin)
    plt.figure(figsize=(5,3))
    sn.heatmap(cf_binary_matrix, annot=True,  fmt = 'd')
    plt.title('Confusion matrix for test data')
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.show()

def PlayerMLPClassifier(X_train, y_train, X_test, y_test):
    print("--------------MLP ---------------")
    mlp_classif = MLPClassifier(activation = 'tanh',hidden_layer_sizes = (4,), solver = 'sgd', learning_rate = 'constant', max_iter = 2000)
    cv_mlp_scores = cross_val_score(mlp_classif, X_train, y_train, cv = 10)
    mlp_classif.fit(X_train, y_train)
    print('Train Accuracy : %.3f'%mlp_classif.score(X_train, y_train))
    print('Test Accuracy : %.3f'%mlp_classif.score(X_test, y_test))
    return ConfidenceInterval(cv_mlp_scores)

def PlayerRandomForestClassifierGrid(X_train, y_train, X_test, y_test):
    print("--------------RANDOM FOREST GRID---------------")
    params = {'n_estimators': [50],
            'criterion' : ['entropy'],
            'max_depth' : [10, 15, 8],
            'min_samples_split' : [2, 4, 8]
         }
    rf_classif_grid = GridSearchCV(RandomForestClassifier(random_state=RANDOM_STATE), param_grid=params, n_jobs=-1, cv=8, verbose=5)
    rf_classif_grid.fit(X_train,y_train)
    print('Train Accuracy : %.3f'%rf_classif_grid.best_estimator_.score(X_train, y_train))
    print('Test Accuracy : %.3f'%rf_classif_grid.best_estimator_.score(X_test, y_test))
    print('Best Accuracy Through Grid Search : %.3f'%rf_classif_grid.best_score_)
    print('Best Parameters : ',rf_classif_grid.best_params_)

def RFClassifier(X_train, y_train, X_test, y_test, weights = None):
    print("--------------RF ---------------")
    #weights = [1 + (index/1000) for index in range(len(y_train))]
    rf_classif = RandomForestClassifier(n_estimators= 50, criterion= "entropy", max_depth= 15, min_samples_split = 8)
    cv_rf_scores = cross_val_score(rf_classif, X_train, y_train, cv = 10)
    rf_classif.fit(X_train, y_train, sample_weight= weights)
    print('Train Accuracy : %.3f'%rf_classif.score(X_train, y_train))
    print('Test Accuracy : %.3f'%rf_classif.score(X_test, y_test))
    return ConfidenceInterval(cv_rf_scores)

def SVMClassifierGrid(X_train, y_train, X_test, y_test):
    print("--------- SVM GRID ------------")
    params = {'C': [4, 2, 3], 
            'gamma': [0.001, 0.002, 0.0005], 
            'kernel': ['rbf', 'linear']}
    svm_classif_grid = GridSearchCV(svm.SVC(random_state=RANDOM_STATE), param_grid=params, n_jobs=-1, cv=8, verbose=5)
    svm_classif_grid.fit(X_train,y_train)
    print('Train Accuracy : %.3f'%svm_classif_grid.best_estimator_.score(X_train, y_train))
    print('Test Accuracy : %.3f'%svm_classif_grid.best_estimator_.score(X_test, y_test))
    print('Best Accuracy Through Grid Search : %.3f'%svm_classif_grid.best_score_)
    print('Best Parameters : ',svm_classif_grid.best_params_)    

def SVMClassifier(X_train, y_train, X_test, y_test, weights = None):
    print("--------------SVM ---------------")
    #weights = [1 + (index/1000) for index in range(len(y_train))]
    svm_classif = svm.SVC(C = 4, gamma = 0.002, kernel = "rbf")
    cv_svm_scores = cross_val_score(svm_classif, X_train, y_train, cv = 10)
    svm_classif.fit(X_train, y_train, sample_weight= weights)
    print('Train Accuracy : %.3f'%svm_classif.score(X_train, y_train))
    print('Test Accuracy : %.3f'%svm_classif.score(X_test, y_test))
    return ConfidenceInterval(cv_svm_scores)



def LogRegressClassifierGrid(X_train, y_train, X_test, y_test):
    print("--------------LOG REGRESS GRID---------------")
    params = {
            "solver": ["newton-cg", "lbfgs", "liblinear", "sag", "saga"],
            "penalty" : ["l1", "l2", "elasticnet"],
            "C" : [1, 2, 3, 4]
             }
    lr_classif_grid = GridSearchCV(linear_model.LogisticRegression(random_state=RANDOM_STATE), param_grid=params, n_jobs=-1, cv=8, verbose=5)
    lr_classif_grid.fit(X_train,y_train)
    print('Train Accuracy : %.3f'%lr_classif_grid.best_estimator_.score(X_train, y_train))
    print('Test Accuracy : %.3f'%lr_classif_grid.best_estimator_.score(X_test, y_test))
    print('Best Accuracy Through Grid Search : %.3f'%lr_classif_grid.best_score_)
    print('Best Parameters : ',lr_classif_grid.best_params_)

def LogRegressClassifier(X_train, y_train, X_test, y_test, weights = None):
    print("--------------LOG REGRESS ---------------")
    #weights = [log2(index+1) for index in range(len(y_train))]
    lr_classif = linear_model.LogisticRegression(penalty= "l2", solver= "newton-cg", max_iter= 5000, C= 2)
    cv_svm_scores = cross_val_score(lr_classif, X_train, y_train, cv = 10)
    lr_classif.fit(X_train, y_train, sample_weight= weights)
    print('Train Accuracy : %.3f'%lr_classif.score(X_train, y_train))
    print('Test Accuracy : %.3f'%lr_classif.score(X_test, y_test))
    return ConfidenceInterval(cv_svm_scores)

def GetMostImportantFeatures(X_train, y_train, feature_num = 100):
    regr = ElasticNetCV(cv=8, random_state=RANDOM_STATE, max_iter= 5000)
    regr.fit(X_train, y_train)
    coeff_pairs = list(zip(regr.coef_, list(range(len(regr.coef_)))))
    sorted_coeff_pairs = sorted(coeff_pairs, key = lambda x : - abs(x[0]))
    important_indices = [pair[1] for pair in sorted_coeff_pairs[:feature_num]]
    important_predictors = [X_train.columns[index] for index in important_indices]
    return important_predictors

def plotElasticNet(X_train, y_train, num_of_features = 10):
    regr = ElasticNetCV(cv=5, random_state=RANDOM_STATE, max_iter= 5000)
    regr.fit(X_train, y_train)
    coeff_pairs = list(zip(regr.coef_, list(range(len(regr.coef_)))))
    sorted_coeff_pairs = sorted(coeff_pairs, key = lambda x : - abs(x[0]))
    important_indices = [pair[1] for pair in sorted_coeff_pairs[:num_of_features]]
    important_predictors = [X_train.columns[index] for index in important_indices]
    n_alphas = 200
    alphas = np.logspace(-10, -1, n_alphas)
    coefs = []
    for a in alphas:
        elNet = linear_model.ElasticNet(alpha=a, fit_intercept=False)
        elNet.fit(X_train, y_train)
        coefs.append([elNet.coef_[important_index] for important_index in important_indices])
    ax = plt.gca()
    ax.plot(alphas, coefs)
    ax.set_xscale("log")
    #ax.set_xlim(ax.get_xlim()[::-1])  # reverse axis
    plt.xlabel("alpha")
    plt.ylabel("weights")
    plt.legend(important_predictors)
    plt.title("Regression coefficients as a function of the regularization")
    plt.axis("tight")
    plt.show()
    

def ConfidenceInterval(data):
    data_mean = data.mean()
    std = sqrt((sum([(data_mean - sample)**2 for sample in data]))/(len(data) * (len(data)-1)))
    alpha = 95
    tVal = t.ppf((alpha+100)/200,len(data)-1)
    print(f"Mean: {data_mean}")
    print(f"95 Confidence interval: ({data_mean - tVal*std }, {data_mean + tVal*std})")
    return (data_mean - tVal*std, data_mean, data_mean + tVal*std)

def plotRegularizationInCV(classifyFuncCV, X_train_orig, y_train_orig, processed_data, target_column):
    REGUL_FEATURES_COUNTS = [16, 32, 64, 96, 128, 160, 192, 224, 256, 288, 320]
    lower_bs, means, upper_bs = list(), list(), list()
    for reg_feature_count in REGUL_FEATURES_COUNTS:
        important_predictors = GetMostImportantFeatures(X_train_orig, y_train_orig, reg_feature_count)
        X_train, X_test, y_train, y_test = train_test_split(processed_data[important_predictors], processed_data[target_column], test_size= TEST_SIZE, random_state= RANDOM_STATE, shuffle = SHUFFLE) 
        (lower, mean, upper) = classifyFuncCV(X_train, y_train, X_test, y_test)
        lower_bs.append(lower)
        means.append(mean)
        upper_bs.append(upper)
    plt.fill_between(REGUL_FEATURES_COUNTS, lower_bs, upper_bs, color = 'yellow', alpha = 0.3)
    plt.title("Confidence intervals for the accuracies of the best model based on number of features")
    plt.scatter(REGUL_FEATURES_COUNTS, lower_bs, color = 'yellow')
    plt.plot(REGUL_FEATURES_COUNTS, means, color = 'blue')
    plt.xlabel("feature count")
    plt.ylabel("accuracy")
    plt.scatter(REGUL_FEATURES_COUNTS, means, color = 'blue')
    plt.scatter(REGUL_FEATURES_COUNTS, upper_bs, color = 'yellow')
    plt.show()

def split_data(encoded_matches, predictors, target):
    #encoded_matches.sort_index(inplace = True)
    X_train, X_test, y_train, y_test = train_test_split(
    encoded_matches[predictors],
    encoded_matches[target],
    test_size= TEST_SIZE,
    random_state= RANDOM_STATE,
    shuffle= SHUFFLE)
    if not(SYMETRIC):
        return (X_train, X_test, y_train, y_test)
    
    sym_encoded_matches = Hot_one_input(players_by_map, symetrical= True, debug=False)  #.sort_index()
    y_train = sym_encoded_matches.loc[X_train.index, [target]][target]
    X_train = sym_encoded_matches.loc[X_train.index, predictors]
    return (X_train, X_test, y_train, y_test)

YEAR_TO_INCLUDE = 2020

df_maps = Read_from_csvs(MAP_FILE)
df_players = Read_from_csvs(PLAYER_FILES)
df_players = df_players[df_players.tournament_title == TOURNAMENT]

if DEBUG:
    print('players count ',len(df_players["player_name"].unique()))

players_by_stats =Get_players_stats(df_players,normalize='std',debug=DEBUG)
players_by_map = Get_players_by_matches_played(df_maps, df_players,debug=DEBUG)

#NAIVE CLASSIFIER
df_grouped_maps = players_by_map[["match_id", "game_number", "team_one_name", "team_two_name", "map_winner", "map_name"]].drop_duplicates()
target_column = "map_winner" 
predictors= ["team_one_name", "team_two_name"]
team_data = df_grouped_maps[predictors + [target_column]]
X_train, X_test, y_train, y_test = train_test_split(
    team_data[predictors],
    team_data[target_column],
    test_size=TEST_SIZE, random_state=RANDOM_STATE, shuffle=SHUFFLE
    )
TrivialMFClassifier(X_train, y_train, X_test, y_test)

#PLAYERS ONE HOT ENC

processed_data_stats = Player_stats_input(players_by_map,players_by_stats,DEBUG)

if DEBUG:
    print('Player stats coding')
    print(processed_data_stats)

# processed_data_2.to_csv('matchers_by_stats.csv',index=False)
# players_by_stats.to_csv('player_by_stats.csv',index=False)


target_column = 'result' 
encoded_matches = Hot_one_input(players_by_map, symetrical= False, debug=DEBUG)
predictors = list(set(list(encoded_matches.columns)) - set([target_column]))
(X_train, X_test, y_train, y_test) = split_data(encoded_matches, predictors, target_column)

#SVMClassifier(X_train, y_train, X_test, y_test)
#LogRegressClassifier(X_train, y_train, X_test, y_test)

#FIND IMPORTANT PREDICTORS AND PLOT REGULARIZATION

#plotRegularizationInCV(SVMClassifier, X_train, y_train, encoded_matches, target_column)
#plotRegularizationInCV(PlayerMLPClassifier, X_train, y_train, encoded_matches, target_column)
#plotRegularizationInCV(LogRegressClassifier, X_train, y_train, encoded_matches, target_column)
plotRegularizationInCV(RFClassifier, X_train, y_train, encoded_matches, target_column)

important_predictors = GetMostImportantFeatures(X_train, y_train, REGUL_FEATURES_COUNT)
#plotElasticNet(X_train, y_train)

#USE IMPORTANT PREDICTORS ONLY

print("-------- REGULARIZATION ------")

(X_train, X_test, y_train, y_test) = split_data(encoded_matches, important_predictors, target_column)


#GRID SEARCHES
#print("-----------GRID SEARCHING -----------")
#PlayerMLPClassifierGrid(X_train, y_train, X_test, y_test)

PlayerRandomForestClassifierGrid(X_train, y_train, X_test, y_test)
RFClassifier(X_train, y_train, X_test, y_test)

#SVMClassifierGrid(X_train, y_train, X_test, y_test)

#LogRegressClassifierGrid(X_train, y_train, X_test, y_test)

SVMClassifier(X_train, y_train, X_test, y_test)
PlayerMLPClassifier(X_train, y_train, X_test, y_test)
LogRegressClassifier(X_train, y_train, X_test, y_test)

#NO PLAYERS INCLUDED
predictors = list((set(list(encoded_matches.columns)) - set(df_players["player_name"].unique())) - set([target_column]))
X_train, X_test, y_train, y_test = train_test_split(encoded_matches[predictors], encoded_matches[target_column], test_size= TEST_SIZE, random_state= RANDOM_STATE, shuffle= SHUFFLE) 

print("------- NO PLAYER DATA INCLUDED ----- ")
PlayerMLPClassifier(X_train, y_train, X_test, y_test)
