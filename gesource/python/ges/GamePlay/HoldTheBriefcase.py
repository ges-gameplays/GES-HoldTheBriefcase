from GamePlay import GEScenario
import GEEntity, GEPlayer, GEUtil, GEWeapon, GEMPGameRules, GEGlobal, GEGamePlay
from .Utils.GEWarmUp import GEWarmUp
from GEWeapon import CGEWeapon

USING_API = GEGlobal.API_VERSION_1_2_0

# Created by Euphonic for GoldenEye: Source 5.0
# For more information, visit https://euphonic.dev/goldeneye-source/

#	* / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / *
HoldTheBriefcaseVersion = "^uHold the Briefcase Version ^l5.1.0"
#	* / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / *

class Case( object ):
	"""Handles information about each case"""
	
	def __init__( self, player ):
		self.owner = player
	
	def update( self ):
		if self.owner:
			self.owner.AddRoundScore( 1 )
			if GEMPGameRules.IsTeamplay():
				return self.owner.GetTeamNumber()
		return None

class HoldTheBriefcase( GEScenario ):
	
	def __init__( self ):
		super( HoldTheBriefcase, self ).__init__()
		
		self.warmupTimer = GEWarmUp( self )
		self.notice_WaitingForPlayers = 0
		self.WaitingForPlayers = True

		self.teamScoringTimer = 100
		self.TokenClass = "token_deathmatch"
		
		self.RoundActive = False
		
		self.caseDict = {}
		
		self.prevCount = 0
		self.nextCheckTime = -1
		
		self.roundScoreJanus = 0
		self.roundScoreMI6 = 0
		
#		>> Colors >>
		self.colorMsg = GEUtil.CColor(255,255,255,240)
		self.colorCase = GEUtil.CColor(230,230,230,240)
		self.colorMI6 = GEUtil.CColor(0,150,255,255)
		self.colorJanus = GEUtil.CColor(255,0,0,255)
		self.scoreboardDefault = GEGlobal.SB_COLOR_NORMAL
		self.scoreboardOwner = GEGlobal.SB_COLOR_WHITE
		
#		>> Messages & Text
		self.caseName = "Briefcase"
		self.dropText = " ^1dropped a ^u" + self.caseName
		self.grabText = " ^1picked up a ^u" + self.caseName
		self.pickText = "Picked up a " + self.caseName
	
	def GetPrintName( self ):
		return "Hold the Briefcase"

	def GetScenarioHelp( self, help_obj ):
		help_obj.SetDescription( "Grab a briefcase and hold it for as long as you can.\n\nAlternative Scoring: Get a point for each kill while holing the briefcase.\n\nAlternative Scoring: Get an extra point for each kill while holding the briefcase\n\nTeamplay: Toggleable\n\nCreated by WNxEuphonic" )
		help_obj.SetInfo("Hold the briefcase for as long as you can", "" )

	def GetGameDescription( self ):
		if GEMPGameRules.IsTeamplay():
			return "Team Hold the Briefcase"
		else:
			return "Hold the Briefcase"

	def GetTeamPlay( self ):
		return GEGlobal.TEAMPLAY_TOGGLE

	def OnLoadGamePlay( self ):
		self.CreateCVar( "hb_warmup", "20", "The warm up time in seconds (Use 0 to disable warmup)" )
		self.CreateCVar( "hb_scoring", "0", "Set to 0 to use briefcase hold duration, 1 to use kills while holding briefcase" )
		self.CreateCVar( "hb_normal_points", "1", "Gives a point or some time for kills while not holding the briefcase" )
		self.CreateCVar( "hb_cases_override", "0", "Sets number of cases to spawn. Set to 0 to use default amount. Max 10" )
		
		GEUtil.PrecacheSound( "GEGamePlay.Token_Grab" )
		
		GEMPGameRules.GetRadar().SetForceRadar( True )
		GEMPGameRules.DisableSuperfluousAreas()
		
		if int( GEUtil.GetCVarValue( "hb_scoring" ) ) == 0:
			GEMPGameRules.EnableTimeBasedScoring()
				
		if GEMPGameRules.GetNumActivePlayers() >= 2:
			self.WaitingForPlayers = False
		
		GEMPGameRules.GetTokenMgr().SetupToken( self.TokenClass, limit= self.getCaseLimit(), team = GEGlobal.TEAM_NONE,
							location = GEGlobal.SPAWN_TOKEN,
							glow_color = self.colorCase, glow_dist=450.0,
							allow_switch = True, respawn_delay=35.0,
							view_model="models/weapons/tokens/v_briefcasetoken.mdl",
							world_model="models/weapons/tokens/w_briefcasetoken.mdl",
							print_name= self.caseName )

	def OnUnloadGamePlay( self ):
		self.hideHold( None )

	def OnRoundBegin(self):
		self.caseDict = {}
		GEMPGameRules.ResetAllPlayersScores()
		self.RoundActive = True
		GEMPGameRules.GetTokenMgr().SetupToken( self.TokenClass, limit= self.getCaseLimit() )
		
		self.roundScoreJanus = 0
		self.roundScoreMI6 = 0
		
		if GEMPGameRules.GetNumActivePlayers() > 1:
			self.RoundActive = True
	
	def OnRoundEnd(self):
		GEMPGameRules.GetRadar().DropAllContacts()
		GEMPGameRules.GetTokenMgr().SetupToken( self.TokenClass, limit=0 )
		self.RoundActive = False
	
	def OnPlayerKilled( self, victim, killer, weapon ):
		# No points if in warmup
		if self.warmupTimer.IsInWarmup() or not victim or not self.RoundActive:
			return
	
		if victim == killer or not killer:
			if int( GEUtil.GetCVarValue( "hb_scoring" ) ) == 0:
				if self.isOwner( victim ):
					victim.IncrementScore( max(-victim.GetScore(), int(-10 - 0.2 * victim.GetScore())) )
				else:
					victim.IncrementScore( max(-victim.GetScore(), -5 ) )
			else:
				if self.isOwner( victim ):
					victim.IncrementScore( -2 )
				else:
					victim.IncrementScore( -1 )
			return
		
		elif int( GEUtil.GetCVarValue( "hb_scoring" ) ) != 0:
			reward = 0
			if int( GEUtil.GetCVarValue( "hb_normal_points")) != 0:
				reward += 1
				if self.isOwner( victim ):
					reward += 1
			if self.isOwner( killer ):
				reward += 1
			killer.IncrementScore( reward )
			if GEMPGameRules.IsTeamplay() and reward:
					GEMPGameRules.GetTeam( killer.GetTeamNumber() ).IncrementRoundScore( reward )
			return
		
		elif int( GEUtil.GetCVarValue("hb_normal_points")):
			killer.IncrementScore( 5 )
			if GEMPGameRules.IsTeamplay():
				self.updateTeamScores(killer.GetTeamNumber(), points = 5)
			return

		return

	def OnCVarChanged( self, cvar, previous, current ):
		if cvar == "hb_cases_override" and not self.warmupTimer.IsInWarmup() and GEMPGameRules.GetNumActivePlayers() > 1 and self.RoundActive:
			GEMPGameRules.GetTokenMgr().SetupToken( self.TokenClass, limit= self.getCaseLimit() )
		
		elif cvar == "hb_scoring" and previous != current:
			if current == 0:
				GEMPGameRules.EnableTimeBasedScoring()
			else:
				GEMPGameRules.EnableStandardScoring()
			GEMPGameRules.EndRound()
				
	def OnTokenSpawned( self, token ):
		GEMPGameRules.GetRadar().AddRadarContact( token, GEGlobal.RADAR_TYPE_TOKEN, True, "", self.colorCase )
		GEMPGameRules.GetRadar().SetupObjective( token, GEGlobal.TEAM_NONE, "!" + self.TokenClass, self.caseName, self.colorCase, 0, True )
	
	def OnTokenRemoved( self, token ):
		GEMPGameRules.GetRadar().DropRadarContact( token )
		ID = str( GEEntity.GetUID( token ) )
		if ID in self.caseDict:
			if self.caseDict[ ID ].owner:
				self.hideHold( self.caseDict[ ID ].owner )
				GEMPGameRules.GetRadar().DropRadarContact( self.caseDict[ ID ].owner )
				GEMPGameRules.GetRadar().ClearObjective( self.caseDict[ ID ].owner )
				self.caseDict[ ID ].owner.SetScoreBoardColor( self.scoreboardDefault )
			del self.caseDict[ ID ]
	
	def OnTokenPicked( self, token, player ):
		ID = str( GEEntity.GetUID( token ) )
		self.caseDict[ ID ] = Case( player )
		self.displayHold(player)
		
		GEUtil.PlaySoundToPlayer( player, "GEGamePlay.Token_Grab", True )
		GEUtil.HudMessage( player, self.pickText, -1, 0.67, self.colorMsg, 2.5, 1 )
		
		GEMPGameRules.GetRadar().DropRadarContact( token )
		GEMPGameRules.GetRadar().AddRadarContact( player, GEGlobal.RADAR_TYPE_PLAYER, True, "sprites/hud/radar/run", self.getColor(player) )
		GEMPGameRules.GetRadar().SetupObjective( player, GEGlobal.TEAM_NONE, "!" + self.TokenClass, "", self.getColor(player), 0, False )
		
		player.SetScoreBoardColor( self.scoreboardOwner )
		
		GEUtil.PostDeathMessage( self.getTextColor(player) + player.GetCleanPlayerName() + self.grabText )

		GEUtil.EmitGameplayEvent( "hb_casepicked", "%i" % player.GetUserID() )
	
	def OnTokenDropped( self, token, player ):
		ID = str( GEEntity.GetUID( token ) )
		self.caseDict[ ID ] = Case( None )
		self.hideHold(player)

		GEMPGameRules.GetRadar().AddRadarContact( token, GEGlobal.RADAR_TYPE_TOKEN, True, "", self.colorCase )
		GEMPGameRules.GetRadar().SetupObjective( token, GEGlobal.TEAM_NONE, "!" + self.TokenClass, self.caseName, self.colorCase )

		GEMPGameRules.GetRadar().DropRadarContact( player )
		GEMPGameRules.GetRadar().ClearObjective( player )

		player.SetScoreBoardColor( self.scoreboardDefault )
		
		GEUtil.PostDeathMessage( self.getTextColor(player) + player.GetCleanPlayerName() + self.dropText )
		
		GEUtil.EmitGameplayEvent( "hb_casedropped", "%i" % player.GetUserID() )
	
	def OnThink(self):
		if int(GEUtil.GetCVarValue( "hb_scoring" )) == 0 and self.RoundActive:
			curtime = GEUtil.GetTime()
			if curtime >= self.nextCheckTime:
				self.updateTimers()
				self.nextCheckTime = curtime + 1.0
		
		if GEMPGameRules.GetNumActivePlayers() < 2:
			if not self.WaitingForPlayers:
				self.notice_WaitingForPlayers = 0
				GEMPGameRules.EndRound()
			elif GEUtil.GetTime() > self.notice_WaitingForPlayers:
				GEUtil.HudMessage( None, "#GES_GP_WAITING", -1, -1, self.colorMsg, 2.5, 1 )
				self.notice_WaitingForPlayers = GEUtil.GetTime() + 12.5

			self.warmupTimer.Reset()
			self.WaitingForPlayers = True
			return

		elif self.WaitingForPlayers:
			self.WaitingForPlayers = False
			if not self.warmupTimer.HadWarmup():
				self.warmupTimer.StartWarmup( int( GEUtil.GetCVarValue( "hb_warmup" ) ), True )
				if self.warmupTimer.IsInWarmup():
					GEUtil.EmitGameplayEvent( "hb_startwarmup" )
			else:
				GEMPGameRules.EndRound( False )
		else:
			if abs( GEMPGameRules.GetNumActivePlayers() - self.prevCount ) > 0 and not self.warmupTimer.IsInWarmup() and self.RoundActive:
				GEMPGameRules.GetTokenMgr().SetupToken( self.TokenClass, limit= self.getCaseLimit() )
	
	def OnPlayerSay(self, player, text):
		if text == "!version":
			GEUtil.ClientPrint(player, GEGlobal.HUD_PRINTTALK, HoldTheBriefcaseVersion)
	

	# # # # # # CUSTOM FUNCTIONS # # # # # #
	
	
	def getCaseLimit(self):
		cvarValue = min(int(GEUtil.GetCVarValue( "hb_cases_override" )), 10)
		playerCount = GEMPGameRules.GetNumActivePlayers()
		self.prevCount = playerCount
		
		if cvarValue > 0 and playerCount > 1:
			return cvarValue
		else:
			if playerCount < 2:
				return 0
			if playerCount < 10:
				return 1
			elif playerCount < 15:
				return 2
			elif playerCount < 22:
				return 3
			else:
				return 4
	
	def getColor(self, player):
		if GEMPGameRules.IsTeamplay():
			if player.GetTeamNumber() == GEGlobal.TEAM_JANUS:
				return self.colorJanus
			elif player.GetTeamNumber() == GEGlobal.TEAM_MI6:
				return self.colorMI6
		else:
			return self.colorCase
	
	def getTextColor(self, player):
		if GEMPGameRules.IsTeamplay():
			if player.GetTeamNumber() == GEGlobal.TEAM_JANUS:
				return "^r"
			elif player.GetTeamNumber() == GEGlobal.TEAM_MI6:
				return "^i"
		else:
			return "^7"
	
	def updateTimers(self):
		for item in self.caseDict:
			self.updateTeamScores( self.caseDict[ item ].update() )
	
	def updateTeamScores(self, team, points = 1):
		if not team:
			return
		elif team == GEGlobal.TEAM_JANUS:
			self.roundScoreJanus += points
			while self.roundScoreJanus >= 10:
				GEMPGameRules.GetTeam(GEGlobal.TEAM_JANUS).IncrementRoundScore( 1 )
				self.roundScoreJanus -= 10
		elif team == GEGlobal.TEAM_MI6:
			self.roundScoreMI6 += points
			while self.roundScoreMI6 >= 10:
				GEMPGameRules.GetTeam(GEGlobal.TEAM_MI6).IncrementRoundScore( 1 )
				self.roundScoreMI6 -= 10
	
	def displayHold(self, player):
		GEUtil.HudMessage( player, "[ " + self.caseName + " ]", -1, 0.01, self.getColor(player), float('inf'), 2 ) 
	
	def hideHold(self, player):
		GEUtil.HudMessage( player, "", 0.0, 0.0, self.colorMsg, 0, 2 )
	
	def isOwner(self, player):
		for item in self.caseDict:
			if player == self.caseDict[ item ].owner:
				return True
		return False