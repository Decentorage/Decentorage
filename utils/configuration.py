from datetime import datetime


import datetime


class Configuration:


	#---------------- Avalability and Heartbeat settings ----------------#
	# How many minutes between each heartbeat
	intraheartbeat_minutes = 10
	# Time at which first avalability interval started
	decentorage_epoch = datetime.datetime(2020,1,1)
	# How often does availability reset
	resetting_months = 2
	# Minimum availability to send money
	minimum_availability = 70
