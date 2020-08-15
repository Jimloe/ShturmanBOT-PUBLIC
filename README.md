# ShturmanBOT

ShturmanBOT is being designed as a Discord/Subreddit moderator tool to assist /r/EscapeFromTarkov with catching posts that violate the rules,
and to enforce flairs on the subreddit.  It also functions as a dev tracker that'll post notifications in a set Discord channel.  
The following commands will change how the bot runs and performs actions on the fly

%commands with list all the following commands:


%getusers - Shows a list of tracked users
%adduser Xusername TRUE/FALSE - Adds/Updates a user to the tracked user list.  TRUE/FALSE notates whether or not a sticky will be created in the thread they've posted in.
%removeuser Xusername - Removes a user from tracked user list

%devtracker True/False - Enables or disables dev tracking and Discord notifications
%devtrackerstatus - Shows whether or not the dev tracking and Discord notifications are running.
%devchannel add/remove - Adds or removes a channel for Dev post notifications.
%updatetime - Updates the time interval for the Reddit scans

%commentsticky True/False - Enables or disables the Reddit sticky comment functionality.  References the tracked users list.
%commentstickystatus - Shows whether or not the Reddit sticky comment functionality is running.

%nextscan - Displays next run time

%fhb True/False - Enables/disables the enforcement of flairs on subreddit posts.
%fhbint number - Changes the interval of Flair Helper.

%dml True/False - Enables/disables checking the mod log for duplicate actions.
%dmlchannel add/remove - Adds or removes a channel for Duplicate Mod Log notifications.
%dmltype DM/Channel - Specifies whether you want reports to go to a channel or to DM the users.

%r5 True/False - Enables/disables checking new submissions for potential R5 violations.
%r5remove True/False - Enables/disables automatic removal of posts.

%monitor - See how hot my server is running at

%updatemodlist - Scan the mod Discord and see if there's been any changes in the Moderator roles.

%updatesubreddit Xsubname - Change the subreddit that the bot performs MODERATION actions on.  This does not affect dev tracking.
