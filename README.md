![HUNTER](https://i.imgur.com/N2Ru7ib.jpg)

# Hunter Alpha

A modular Telegram Python bot running on python3 with a sqlalchemy database and an entirely themed persona to make Naruto suitable for Anime and Manga group chats. 

Can be found on telegram as [Hunter Alpha (bot)](http://t.me/xxXhunteralphaX_Bot).

The Support group can be reached out to at [Hunter Alpha Support](https://t.me/AlphaEliasxd), where you can ask for help about [Hunter Alpha (bot)](https://t.me/xxXhunteralphaX_Bot), discover/request new features, report bugs, and stay in the loop whenever a new update is available :) 


## How to setup/deploy.

### Read these notes carefully before proceeding 
 - Edit any mentions of [@Hunter Alpha Support](https://t.me/AlphaEliasxd) Support to your own support chat
 - Your code must be open source and a link to your fork's repository must be there in the start reply of the bot [See this](https://github.com/AlphaEliasPY/AlphaHunterDev)
 - Lastly, if you are found to run this repo without the code being open sourced or the repository link not mentioned in the bot, we will push a gban for you in our network because of being in violation of the license, you are free to be a dick and not respect the open source code (we do not mind) but we will not be having you around our chats
 - This repo does not come with technical support, so DO NOT come to us asking help about deploy/console errors


<details>
  <summary>Steps to deploy on Heroku !! </summary>

```
Fill in all the details, Deploy!
Now go to https://dashboard.heroku.com/apps/(app-name)/resources ( Replace (app-name) with your app name )
REMEMBER: Turn on worker dyno (Don't worry It's free :D) & Webhook
Now send the bot /start, If it doesn't respond go to https://dashboard.heroku.com/apps/(app-name)/settings and remove webhook and port.
```

  [![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/AlphaEliasPY/AlphaHunterDev)

</details>  

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https%3A%2F%2Fgithub.com%2FAlphaEliasPY%2FAlphaHunterDev&plugins=postgresql&envs=TOKEN_BOT%2CSQLALCHEMY_DATABASE_URI%2CAPI_ID%2CAPI_HASH%2COWNER_ID%2COWNER_USERNAME%2CSUPPORT_CHAT%2CEVENT_LOGS%2CJOIN_LOGGER%2CCASH_API_KEY%2CTIME_API_KEY%2CDEV_USERS%2Csw_api%2CSTRICT_GBAN%2CSUDO_USERS%2CSUPPORT_USERS%2CWHITELIST_USERS%2CENV%2CWEBHOOK%2CPORTL%2CURL%2CNO_LOAD%2CBL_CHATS%2CALLOW_EXCL%2CDONATION_LINK%2CDEL_CMDS%2CAI_API_KEY%2CBAN_STICKER%2CWALL_API)
