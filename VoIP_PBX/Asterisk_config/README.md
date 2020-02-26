# Configuring Asterisk

Taking a look at `/etc/asterisk` shows just how may configuration files we have to deal with. After spending quite some time going through Asterisk's Wiki we ended up finding the most relevant sections we had to dig into to get a working PBX. These are all listed below.

## Getting some clients registered through `sip.conf`
Asterisk mainly deals with 2 types of what it calls "channel drivers", that is, two ways of managing communications to and from the PBX. We first decided to go along with the newer `PJSIP` driver but later found out how it was less unconvenient that its older counterpart `SIP` when dealing with constantly registering and unregistering clients. We have also found that it's more intuitive to handle these clients with the `sip` command from Asterisk's CLI than working with `pjsip`. That's why we chose to go with the former implementation as it's also better documented. As we have set up Asterisk 17 and it uses `PJSIP` as its default channel driver we needed to play around with `modules.conf` to explicitly unload `res_pjsip` and load `chan_sip` so that there weren't any collisions caused by using both at the same time.

Whin `chan_sip` ready to rock we set out to configure some clients. We decided to use *templates* that allow for configuration reusanility across clients whose settings were pretty much the same. The pertinent configuration can be found in `sip.conf`. We have commented every relevant section so as to clarify the settings and why we chose them. We would like to point out that the language for each user is configured here so that we can have two different people getting different language prompts.

## At the heart of the PBX: `extensions.conf`

