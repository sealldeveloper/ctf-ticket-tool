# CTF Ticket Tool
Hello! This bot was made for one of the CTF teams I play for, [IrisSec](https://irissec.xyz/) originally to make the backend for tickets more organised and ping the correct people, planning usage for IrisCTF 2025 (which you should come to). This is to have a better system for that than regular ticketing bots.

## .env Setup
Firstly, rename the `.env.template` to `.env`, here is a table for the key and value pairs that are expected.

| Key Name                                       | Value Type | Value Options | Optional? | Default Value | Purpose                                      |
|------------------------------------------------|------------|---------------|-----------|---------------|----------------------------------------------|
| TOKEN                                          | String     | -             | No        | -             | The token for your Discord Bot.               |
| GUILD_ID                                       | String     | -             | No        | -             | The ID for the Discord Server your bot is in. |
| ORGANISER_ROLE_ID                              | String     | -             | No        | -             | The role ID for the Administrator role.                   |
| DISCORD_CATEGORY_PER_CHALLENGE_CATEGORY        | Boolean    | 1/0           | No        | -             | If there should be a category for each callenge category. |
| DISCORD_CATEGORY_PER_CHALLENGE_CATEGORY_FORMAT | String     | -             | No        | -             | If the `DISCORD_CATEGORY_PER_CHALLENGE_CATEGORY` is set to `1`, what the category name format should be. Using `<CATEGORY>` to be replaced with the name of the challenge category. |


## Setup
Using the `challenges.json` determines the layout of the tickets channel and ticket creation process. The array at the root of the JSON file has objects of the following.

| Key Name             | Value Type | Value Options    | Optional? | Default Value | Purpose                                                          |
|----------------------|------------|------------------|-----------|---------------|------------------------------------------------------------------|
| name                 | String     | -                | No        | -             | The name of the category.                                        |
| challenges           | Array      | -                | No        | -             | A list of the challenges in the category.                        |
| ping_creators        | Bool       | True/False       | Yes       | False         | If the tickets for this category should ping the creators listed in the challenges. |
| ping_category        | Bool       | True/False       | Yes       | False         | If the tickets for this category should ping the categories role. |


Here is the layout for the challenge objects.

| Key Name             | Value Type | Value Options    | Optional? | Default Value | Purpose                                                          |
|----------------------|------------|------------------|-----------|---------------|------------------------------------------------------------------|
| name                 | String     | -                | No        | -             | The name of the challenge.                                       |
| creators             | Array      | -                | No        | -             | A list of user ID's for the challenge creators.                  |


## Using the bot
This bot was designed on **Python 3.12** but should work on some lower versions.

Firstly install the requirements:
```
python3 -m pip install -r requirements.txt
```

And then run the bot:
```
python3 main.py
```

## To-do
- Add ticket transcripts in a logs channel for CTF admins.

## Known Bugs
- Occasionally defer can trigger and cause commands to partially fail.
