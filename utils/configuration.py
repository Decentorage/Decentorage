import datetime


class Configuration:
	# ____________________Availability and Heartbeat settings_____________________#
	# How many minutes between each heartbeat
	interheartbeat_minutes = 10
	# Time at which first availability interval started
	decentorage_epoch = datetime.datetime(2020, 1, 1)
	# How often does availability reset
	resetting_months = 2
	# Minimum availability to send money
	minimum_availability_threshold = 70
	# Minimum regeneration threshold.
	minimum_regeneration_threshold = 0
	# Storage nodes share
	storage_node_share = 0.75
	# full payment threshold
	full_payment_threshold = 0.95
