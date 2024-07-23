# Stackie bot 

A discord bot made with python that utilizes webscraping Features provided by beautiful soup to exctract the content of the app earn.stackup.dev to keep track of the ongoing and upcoming quests and campaigns!!

## Features

- **Campaign and Quest Notifications**: Automatically notify users about new and upcoming campaigns and quests.
- **Interactive Commands**: Use commands to check ongoing and upcoming campaigns, get help on quests, and more.
- **Knowledge Base Integration**: Get answers to frequently asked questions and update the knowledge base directly from Discord.

## Prerequisites

Before you run the bot, ensure you have the following:

- Python 3.8 or higher
- Required Python libraries (listed in `requirements.txt`)

## Setup

1. **Clone the Repository**:

    ```bash
    git clone https://github.com/yourusername/your-repository.git
    cd your-repository
    ```
2. **Install Required Libraries**:

    ```bash
    pip install -r requirements.txt
    ```

4. **Run the Bot**:

    ```bash
    python stackie.py
    ```

## Bot Operation

The bot will automatically:

- Check for new campaigns and quests every minute.
- Rotate its status every 20 seconds.
- Notify specified channels about new quests and campaigns.

## Bot demonstration
1. Demonstration of the commands: a!ongoing, a!upcoming and a!quest.
   In the following video, the 3 commands have been demonstrated regarding how to use and what to expect as a result
   [Demo video of the three commands](https://youtu.be/BpV9LN_CXpo)

2. Demonstration of the a!chat command
   In the following video, I have demonstrated the process and the possible ways to utilise the command and its features.
  [Demo video of the a!chat command](https://youtu.be/6dBOeDUX9yk)

4. Demonstration of the quest notification on quest days
   In the folowing video I have demonstrated with a created scenario of the date "2024-07-26" As it is a quest day.
   [Demo video of the quest notification feature](https://youtu.be/ioXl6vPhNWU)

5. Demonstration of the new campaign notification whenver a new campaign is added in the app earn.stackup.dev
   In the following video, I have promted the condion as send the notification if the campaign status = "Ongoing" as no Upcoming   
   campaigns were available.
   [Demo video of the new campaign notification feature](https://youtu.be/ViEyArdfx_Q)

   NOTE: Make sure to run the command 'a!add_channel <channel_id>' to specify the notification channel in order to access the   
   notification features.
   
