import sys
sys.path.append(r'C:\Anaconda2\pkgs\gurobi-6.5.2-py27_0\Lib\site-packages\gurobipy')

from gurobipy import *
import csv

from Tkinter import *
import Tkinter as ttk
from ttk import *

Positions = ["QB","RB","WR","TE","D/ST","K"]

NumStarters = {}
NumStarters["QB"] = 1
NumStarters["RB"] = 2
NumStarters["WR"] = 3
NumStarters["TE"] = 1
NumStarters["D/ST"] = 1
NumStarters["K"] = 1
StarterCoeff = 1

NumTier2 = {}
NumTier2["QB"] = 1
NumTier2["RB"] = 2
NumTier2["WR"] = 2
NumTier2["TE"] = 1
NumTier2["D/ST"] = 1
NumTier2["K"] = 0
Tier2Coeff = 0.6

BenchCoeff = 0.2

TotalRosterSize = 16

RELATIVE_VALUES = False; #Make all values relative to best available free agent

def readInCSV(path):
    with open(path, "rU") as f:
        csvFile = csv.reader(f)

        Header = csvFile.next();
        #Index for each column. SENSITIVE TO COLUMN NAMES!!
        indFantasyTeam = Header.index("team")
        indID = Header.index("id")
        indName = Header.index("name")
        indPos = Header.index("position")
        indPercOwned = Header.index("percentOwning")
        indRank = Header.index("positionRank")

        #Below is NF data - may be missing for some players
        indHasNF = Header.index("hasNumberfire")
        indNfRank= Header.index("numberfire_overall_rank")
        indNfProjPts = Header.index("numbefire_fantasy_points") #whoops, typo in script for CSV

        #Stack all values for each time
        FantasyTeams = []
        Rosters = {}
        FreeAgents = {}
        for pos in Positions:
            FreeAgents[pos] = [];

        for row in csvFile:
            jFantasyTeam = row[indFantasyTeam]
            jID = row[indID]
            jName = row[indName]
            jPos = row[indPos]

            jRank = row[indRank]
            #TODO: spit warning
            try:
                jRank = float(jProjPts)
            except:
                jRank = 41;
            jPercOwned = row[indPercOwned]
            try:
                jPercOwned = float(jPercOwned)
            except:
                jPercOwned = 0;

            jHasNF = row[indHasNF]
            jValue = 0;
            if jHasNF == "TRUE":
                jNfRank = int(row[indNfRank])
                jNfProjPts = float(row[indNfProjPts])
                jValue = getValue( jRank, jNfRank, jNfProjPts );
            else:
                jValue = getBasicValue( jRank, jPercOwned );

            jplayer = {}
            jplayer["ID"] = jID;
            jplayer["Name"] = jName;


            jplayer["Value"] = jValue
            jplayer["Val Adj"] = 1; #Default value - may get changed later.

            if jFantasyTeam == "FA":
                #Add player to list of FAs
                FreeAgents[jPos].append(jplayer)

            #Player belongs to a team
            else:
                if jFantasyTeam not in FantasyTeams:
                    #Initialize new fantasy team roster
                    FantasyTeams.append(jFantasyTeam);
                    Rosters[jFantasyTeam] = {};
                    for pos in Positions:
                        Rosters[jFantasyTeam][pos] = [];

                #Add player to appropriate team, position

                Rosters[jFantasyTeam][jPos].append(jplayer)

    if RELATIVE_VALUES:
        #find highest value of free agents at each position
        BestFreeAgentValue = {}
        for pos in Positions:
            BestFreeAgentValue[pos] = 0;
            for player in FreeAgents[pos]:
                BestFreeAgentValue[pos] = max(player["Value"],BestFreeAgentValue[pos]);
        #Reduce roster values by this amount, at each position.
        for team in FantasyTeams:
            for pos in Positions:
                for player in Rosters[team][pos]:
                    player["Value"] = player["Value"]-BestFreeAgentValue[pos]

    return (Rosters, FreeAgents, FantasyTeams)

def findTopFreeAgent(FreeAgents):
    topFA = {}
    for pos in FreeAgents:
        for player in FreeAgents[pos]:
            if(topFA == {}):
                topFA = player
            elif(topFA and player["Value"] > topFA["Value"]):
                print("test")
                topFA = player
    return topFA

def submitRatings():
    ##This will be the command called when the user submits rankings
    print("This will be the command called when the user submits rankings")

    #TODO: Pull personal rankings - may just go into Rosters dict
    # - Other team players will already be there. Just pull your team's adjustments (LHS)
    for player in myPlayerNames:
        playerName = player[0]
        playerPos = player[1]

        for jPlayer in Rosters[myTeam][playerPos]:
            if jPlayer["Name"] == playerName:
                entryValAdj = ratingEntries[playerName].get()
                try:
                    jPlayer["Val Adj"] = float( entryValAdj )
                except:
                    pass #TODO: could throw error if it isn't just empty
    iterateTeams(myTeam, Rosters, FreeAgents, FantasyTeams)

def getValue( Rank, NfRank, NfProjPts ):
    """
    #Wow, this works shitty
    adjRank1 = (max(41-Rank,0)/4)**2;
    adjRank2 = (max(41-NfRank,0)/4)**2;
    value = (adjRank1 + 3*adjRank2)/4 + NfProjPts
    """
    value = NfProjPts/5
    return value

def getBasicValue(Rank,PercentOwned):
    #Use if there are no numberfire projections
    """
    #Wow, this works shitty
    adjRank = (max(41-Rank,0)/4)**2;
    adjPerc = (PercentOwned/20)**2
    value = (adjRank + adjPerc)/2
    """
    value=PercentOwned/10
    return value


def iterateTeams(myTeam, Rosters, FreeAgents, FantasyTeams):
    TradeProposals = []
    for otherTeam in FantasyTeams:
        if otherTeam == myTeam:
            continue;

        findTrade(Rosters[myTeam], Rosters[otherTeam], FreeAgents)
        """
        #TODO: how are these trades stored? what is being returned?
        #TODO: be able to get multiple trades per team
        jTrades = findTrade(Rosters[myTeam], Rosters[otherTeam])
        for jTrade in jTrades:
            TradeProposals.append(jTrade.extend(otherTeam))
        """
    return TradeProposals

def findTrade(myRoster, otherRoster, FreeAgents):
    (AllNames, AllValues, UserVals, Roster, NumPlayersByPos) = stackTeams(myRoster, otherRoster)

    PrevTeamValue = getTeamValue(myRoster, otherRoster)
    topFA = findTopFreeAgent(FreeAgents)
    print(topFA)
    ##Create model
    TradeModel = Model("Trade Test Model")

    Select = {}
    Starter = {}
    Tier2 = {}
    AddFA = {}
    for team in ["Team1","Team2"]:
        Select[team] = {}
        Starter[team] = {}
        Tier2[team] = {}
        for pos in Positions:
            Select[team][pos] = []
            Starter[team][pos] = []
            Tier2[team][pos] = []
            for i in range(NumPlayersByPos[pos]):
                Select[team][pos].append( TradeModel.addVar(vtype = GRB.BINARY, name = "Select_" + team + "_" + pos + "_" + str(i)) )
                Starter[team][pos].append( TradeModel.addVar(vtype = GRB.BINARY, name = "Starter_" + team + "_" + pos + "_" + str(i)) )
                Tier2[team][pos].append( TradeModel.addVar(vtype = GRB.BINARY, name = "Tier2_" + team + "_" + pos + "_" + str(i)) )
        AddFA[team] = TradeModel.addVar(vtype = GRB.BINARY, name = "FreeAgentPickup_" + team)

    TradeModel.update()
    TradeModel.setParam('OutputFlag',False) #stfu


    #Calculate adjusted team value
    TeamValue = {}
    for team in ["Team1","Team2"]:
        TeamValue[team] = 0;
        for pos in Positions:
            for i in range(NumPlayersByPos[pos]):
                if team == "Team1":
                    UserVal = UserVals[pos][i]
                else:
                    UserVal = 1 #Assume other people value consensus
                TeamValue[team] += UserVal * Select[team][pos][i] * AllValues[pos][i] * \
                    (BenchCoeff + (StarterCoeff-BenchCoeff)*Starter[team][pos][i] + (Tier2Coeff-BenchCoeff)*Tier2[team][pos][i])
        TeamValue[team] += AddFA[team]*topFA["Value"]

    Improvement = (TeamValue["Team1"] - PrevTeamValue["Team1"]) + (TeamValue["Team2"] - PrevTeamValue["Team2"])

    TradeModel.setObjective(Improvement, GRB.MAXIMIZE)

    """
    #Assign each player to exactly 1 team
    for pos in Positions:
        for i in range(NumPlayersByPos[pos]):
            TradeModel.addConstr( Select["Team1"][pos][i] + Select["Team2"][pos][i] == 1)
    """
    #TO ADD DROPS:
    #Assign each player to at most 1 team
    for pos in Positions:
        for i in range(NumPlayersByPos[pos]):
            TradeModel.addConstr( Select["Team1"][pos][i] + Select["Team2"][pos][i] <= 1)

    #Starter only if selected
    for team in ["Team1","Team2"]:
        for pos in Positions:
            for i in range(NumPlayersByPos[pos]):
                TradeModel.addConstr( Starter[team][pos][i] <= Select[team][pos][i])

    #Tier2 only if selected
    for team in ["Team1","Team2"]:
        for pos in Positions:
            for i in range(NumPlayersByPos[pos]):
                TradeModel.addConstr( Tier2[team][pos][i] <= Select[team][pos][i])

    #Number of starters at each position
    for team in ["Team1","Team2"]:
        for pos in Positions:
            TradeModel.addConstr( quicksum(Starter[team][pos]) == NumStarters[pos] )

    #Number of tier2 at each position
    for team in ["Team1","Team2"]:
        for pos in Positions:
            TradeModel.addConstr( quicksum(Tier2[team][pos]) <= NumTier2[pos] )

    #Cannot simultaneous start and be tier2
    for team in ["Team1","Team2"]:
        for pos in Positions:
            for i in range(NumPlayersByPos[pos]):
                TradeModel.addConstr( Tier2[team][pos][i] + Starter[team][pos][i] <= 1 )

    #Total roster size
    for team in ["Team1","Team2"]:
        TradeModel.addConstr( quicksum(sum(Select[team][pos]) for pos in Positions) <= TotalRosterSize )


    #Max number of players to trade away
    for team in ["Team1","Team2"]:
        numPlayersTradedAway = 0
        for pos in Positions:
            numPlayersTradedAway += quicksum( Roster[team][pos][i]*(1 - Select[team][pos][i]) for i in range(NumPlayersByPos[pos]))

        TradeModel.addConstr( numPlayersTradedAway <= 3 )
        #TODO: Make above an option on GUI (at most 2 players maybe)

    #Trade beneficial to both teams
    TradeModel.addConstr(TeamValue["Team1"] >= PrevTeamValue["Team1"])
    TradeModel.addConstr(TeamValue["Team2"] >= PrevTeamValue["Team2"])

    #Only add FreeAgent if the team has less than the required number of players
    for team in ["Team1","Team2"]:
        TradeModel.addConstr(AddFA[team] <= quicksum(sum(Select[team][pos]) for pos in Positions) - TotalRosterSize)

    #### OPTIMIZE AND PRINT RESULTS
    TradeModel.optimize()

    #TODO: Put this in a pop-up window
    print '\n\nOPTIMAL SOLUTION\n'
    print 'TEAM 1 Trading Away:'
    PostTeamValue = {}
    PostTeamValue["Team1"] = 0;
    PostTeamValue["Team2"] = 0;

    for pos in Positions:
        for i in range(NumPlayersByPos[pos]):
            if Roster["Team1"][pos][i] == 1 and Select["Team1"][pos][i].X == 0:
                #Look for a drop - other team doesn't own now either
                if Select["Team2"][pos][i].X == 0:
                    print "\t%s: %f DROP \t[%s]"%(pos,AllValues[pos][i],AllNames[pos][i])

                else:
                    print "\t%s: %f\t[%s]"%(pos,AllValues[pos][i],AllNames[pos][i])

            if Select["Team1"][pos][i].X == 1:
                if Starter["Team1"][pos][i].X:
                    PostTeamValue["Team1"] += AllValues[pos][i]*StarterCoeff
                elif Tier2["Team1"][pos][i].X:
                    PostTeamValue["Team1"] += AllValues[pos][i]*Tier2Coeff
                else:
                    PostTeamValue["Team1"] += AllValues[pos][i]*BenchCoeff

    print 'TEAM 2 Trading Away:'
    for pos in Positions:
        for i in range(NumPlayersByPos[pos]):
            if Roster["Team2"][pos][i] == 1 and Select["Team2"][pos][i].X == 0:
                #Look for a drop - other team doesn't own now either
                if Select["Team1"][pos][i].X == 0:
                    print "\t%s: %f DROP \t[%s]"%(pos,AllValues[pos][i],AllNames[pos][i])
                else:
                    print "\t%s: %f\t[%s]"%(pos,AllValues[pos][i],AllNames[pos][i])
            if Select["Team2"][pos][i].X == 1:
                if Starter["Team2"][pos][i].X:
                    PostTeamValue["Team2"] += AllValues[pos][i]*StarterCoeff
                elif Tier2["Team2"][pos][i].X:
                    PostTeamValue["Team2"] += AllValues[pos][i]*Tier2Coeff
                else:
                    PostTeamValue["Team2"] += AllValues[pos][i]*BenchCoeff

    print "\nStarting team values:\n\t\t%f\t%f"%(PrevTeamValue["Team1"],PrevTeamValue["Team2"])
    print "\nEnding team values:\n\t\t%f\t%f"%(PostTeamValue["Team1"],PostTeamValue["Team2"])
    for pos in Positions:
        print pos+":"
        for i in range(NumPlayersByPos[pos]):
            print("\t%f: \t%i (%i)"%(AllValues[pos][i],Select["Team1"][pos][i].X, Starter["Team1"][pos][i].X) ),
            print("\t %i (%i)\t[%s]"%(Select["Team2"][pos][i].X, Starter["Team2"][pos][i].X, AllNames[pos][i]) ),
            print "" #newline

def stackTeams(myRoster, otherRoster):
    ##Stack all values per position
    AllValues = {}
    UserValues = {}
    AllNames = {}
    NumPlayersByPos = {}
    Roster = {}
    Roster["Team1"] = {}
    Roster["Team2"] = {}

    for pos in Positions:
        numPlayers = len(myRoster[pos]) + len(otherRoster[pos])
        Roster["Team1"][pos] = []
        Roster["Team2"][pos] = []
        AllValues[pos] = []
        UserValues[pos] = []
        AllNames[pos] = []
        NumPlayersByPos[pos] = numPlayers
        for i in range(len(myRoster[pos])):
            Roster["Team1"][pos].append(1)
            Roster["Team2"][pos].append(0)
            AllValues[pos].append( myRoster[pos][i]["Value"] )
            UserValues[pos].append( myRoster[pos][i]["Val Adj"] )
            AllNames[pos].append( myRoster[pos][i]["Name"] )
        for i in range(len(otherRoster[pos])):
            Roster["Team1"][pos].append(0)
            Roster["Team2"][pos].append(1)
            AllValues[pos].append( otherRoster[pos][i]["Value"] )
            UserValues[pos].append( otherRoster[pos][i]["Val Adj"] )
            AllNames[pos].append( otherRoster[pos][i]["Name"] )

    return (AllNames, AllValues, UserValues, Roster, NumPlayersByPos)

def getTeamValue(myRoster, otherRoster):
    #Make sure this matches what is done above
    TeamValue = {}
    Values = {}
    UserValues = {}
    for team in ["Team1","Team2"]:
        Values[team] = {};
        UserValues[team] = {};
        TeamValue[team] = 0;
        for pos in Positions:
            Values[team][pos] = [];
            UserValues[team][pos] = [];
    for pos in Positions:
        for player in myRoster[pos]:
            Values["Team1"][pos].append(player["Value"])
            UserValues["Team1"][pos].append(player["Val Adj"])
        for player in otherRoster[pos]:
            Values["Team2"][pos].append(player["Value"])
            UserValues["Team2"][pos].append( 1 ) #Other team: no value adjustment

    for team in ["Team1","Team2"]:
        for pos in Positions:
            Values[team][pos].sort(reverse=True) #Sort descending
            for (i, val) in enumerate(Values[team][pos]):
                if i<NumStarters[pos]:
                    #Starter
                    TeamValue[team] += StarterCoeff*val*UserValues[team][pos][i]
                elif i<NumStarters[pos] + NumTier2[pos]:
                    #Tier2
                    TeamValue[team] += Tier2Coeff*val*UserValues[team][pos][i]
                else:
                    #Bench: discounted value
                    TeamValue[team] += BenchCoeff*val*UserValues[team][pos][i]

    return TeamValue



#if __name__ == "__main__":
args = sys.argv[1:] #strip script name from args
#TODO: handle custom arguments
if len(args)<1:
    csvPath = "data.csv"
else:
    csvPath = args[0]

if len(args)<2:
    myTeam = "ENTH"
else:
    myTeam = args[1]

(Rosters, FreeAgents, FantasyTeams) = readInCSV(csvPath);

#Build player universe
myPlayerNames = []
otherPlayerNamesDict = {}
otherPlayerNames = []
for pos in Positions:
    for player in Rosters[myTeam][pos]:
        myPlayerNames.append([player["Name"], pos])
    otherPlayerNamesDict[pos] = []
    for team in FantasyTeams:
        if team==myTeam:
            continue;
        for player in Rosters[team][pos]:
            otherPlayerNames.append([player["Name"], pos])
            otherPlayerNamesDict[pos].append(player["Name"])

#run_gui()
FFgui = Tk()
FFgui.title("Fantasy Football Trade Optimizer")

totalAdjustments = 0
#Initialize Grid Size
FFgui.geometry("750x550")

#Enable Resizing of the Grid
FFgui.columnconfigure(0, weight = 1)

#Build Title Labels
myRoster = Label(FFgui, text = "My Roster")
myRoster.grid(row = 0, column = 0, columnspan = 3, padx = 50, pady=20)

LeagueAdj = Label(FFgui, text = "League Adjustments")
LeagueAdj.grid(row = 0, column = 3, columnspan = 3, padx = 50, pady=20)

Position = Label(FFgui, text = "Position")
Position.grid(row = 1, column = 0)

PlayerLeft = Label(FFgui, text = "Player")
PlayerLeft.grid(row = 1, column = 1)

Rating = Label(FFgui, text = "Enter Player Value")
Rating.grid(row = 1, column = 2)

PlayerRight = Label(FFgui, text = "Player")
PlayerRight.grid(row = 1, column = 3)

TradeValue = Label(FFgui, text = "Trade Value")
TradeValue.grid(row = 1, column = 4)


#Build DropDown Box
playerNameVar = StringVar(FFgui)
playerNameVar.set(otherPlayerNames[0][0])

playerMenuButton = Menubutton(FFgui, textvariable=playerNameVar)
playerTopMenu = Menu(playerMenuButton, tearoff=False)
playerMenuButton.configure(menu=playerTopMenu)

for key in sorted(otherPlayerNamesDict.keys()):
    jMenu = Menu(playerTopMenu)
    playerTopMenu.add_cascade(label=key, menu=jMenu)
    for value in otherPlayerNamesDict[key]:
        jMenu.add_radiobutton(label=value, variable = playerNameVar, value=value)

    playerMenuButton.pack()

#changeValue = OptionMenu(FFgui, var, *(player[0] for player in otherPlayerNames))
#changeValue = OptionMenu(FFgui, var, *otherPlayerNamesDict)



#changeValue.grid(row = 2, column =3)
playerMenuButton.grid(row = 2, column =3)

TradeValue = StringVar()
# Bind TradeValue instead of var
Value_ent = Entry(FFgui, width = 30)
Value_ent.grid(column = 4, row = 2)

numAdjustments = 0
adjustmentLabels = {}
def addAdjustment(event):
    ##This command is called when the user submits rankings
    global numAdjustments
    numAdjustments +=1
    #TODO: Save value to roster adjustment dict
    player_name = playerNameVar.get()
    player_val = Value_ent.get()
    if player_name not in adjustmentLabels.keys():
        #Add new item
        adjustmentLabels[player_name]={}
        adjustmentLabels[player_name]["NameText"] = Label(FFgui, text = player_name)
        adjustmentLabels[player_name]["ValueText"]= Label(FFgui, text = player_val)
        adjustmentLabels[player_name]["NameText"].grid(column = 3, row = 2 + numAdjustments, sticky = E)
        adjustmentLabels[player_name]["ValueText"].grid(column = 4, row = 2 + numAdjustments, sticky = W)
    else:
        #Update existing item
        adjustmentLabels[player_name]["ValueText"].config(text=player_val)

    #Label_1 = Label(FFgui, text = player_name)
    #Label_2 = Label(FFgui, text = player_val)
    #Label_1.grid(column = 3, row = 2 + numAdjustments, sticky = E)
    #Label_2.grid(column = 4, row = 2 + numAdjustments,sticky = W)

    for team in FantasyTeams:
        for pos in Positions:
            for (i,player) in enumerate(Rosters[team][pos]):
                if player["Name"] == player_name:
                    Rosters[team][pos][i]["Val Adj"] = float(player_val)

#Add Button
addButton = Button(FFgui, text = "Add")
addButton.bind("<Button-1>", addAdjustment)
addButton.grid(row = 2, column = 5, padx = 20)



#Add Main Menu with Submit Button
menu = Menu(FFgui)
FFgui.config(menu = menu)

submitMenu = Menu(menu)
menu.add_cascade(label = "File",menu = submitMenu)
submitMenu.add_command(label = "SUBMIT RANKINGS", command = submitRatings)


#Automatically Populate My Roster
count = 0
ratingEntries = {}
for player in myPlayerNames: #Pull my roster
    #Player Labels
    #player = "Player" + i
    playerLabel = Label(FFgui, text = player[0])
    playerLabel.grid(row = 2+count, column = 0)


    #Player Positions
    #position = "Position" +i
    positionLabel = Label(FFgui, text = player[1])
    positionLabel.grid(row = 2+count, column = 1)

    #Entry
    ratingEntries[player[0]] = Entry(FFgui) #Key = player name
    ratingEntries[player[0]].grid(row=2+count, column = 2)
    count += 1



FFgui.mainloop()

    #iterateTeams(myTeam, Rosters, FreeAgents, FantasyTeams)
