import re
import pandas as pd

def preprocess(data, is_ios):  
    # Define common patterns and replacements
    unwanted_patterns = [
        r'sticker omitted',
        r'image omitted',
        r'video omitted',
        r'audio omitted',
    ]

    # Helper function to replace periods in the dataframe
    def add_period_column(df):
        df['period'] = df['hour'].apply(lambda h: f'{h:02d}-{(h + 1) % 24:02d}')
        return df

    if is_ios:
        # Remove unwanted characters and marks
        data = re.sub(r'[\u200e\u200f\u00a0\u200b]', '', data)  # Combined regex patterns
        data = re.sub(r'\s+', ' ', data)  # Replace multiple spaces with a single space

        # Remove unwanted messages
        for pattern in unwanted_patterns:
            data = re.sub(rf'\[\d{{2}}/\d{{2}}/\d{{2}}, \d{{1,2}}:\d{{2}}:\d{{2}} (?:AM|PM)\] [^:]+?: {pattern}.*?(?=\[\d{{2}}/\d{{2}}/\d{{2}}, \d{{1,2}}:\d{{2}}:\d{{2}} (?:AM|PM)\]|\Z)', '', data)

        # Refined regex pattern to capture username and messages
        message_pattern = r'\[\d{2}/\d{2}/\d{2}, \d{1,2}:\d{2}:\d{2} (?:AM|PM)\] ([^:]+?):\s*(.*?)(?=\[\d{2}/\d{2}/\d{2}, \d{1,2}:\d{2}:\d{2} (?:AM|PM)\]|\Z)'

        # Extract messages with usernames from the entire data
        messages = re.findall(message_pattern, data)

        # Process and replace 'joined using group\'s invite link' messages
        processed_messages = [
            f"{'group_notification' if 'joined using this group\'s invite link' in msg or 'Messages and calls are end-to-end encrypted.' in msg else user}: {msg.replace('~', '')}"
            for user, msg in messages
        ]

        # Extract date and time
        date_time_pattern = r'\[(\d{2}/\d{2}/\d{2}), (\d{1,2}:\d{2}:\d{2} (?:AM|PM))\]'
        date_times_combined = [f"{date}, {time}" for date, time in re.findall(date_time_pattern, data)]

        # Convert to DataFrame
        df = pd.DataFrame({'user_message': processed_messages, 'date': date_times_combined})
        df['date'] = pd.to_datetime(df['date'], format='%d/%m/%y, %I:%M:%S %p')
        df[['user', 'message']] = df['user_message'].str.split(': ', n=1, expand=True)
        df = df.drop(columns=['user_message'])

    else:
        # Remove unwanted characters
        data = re.sub(r'\u202f', ' ', data)

        # Split lines and initialize lists
        lines = data.strip().split('\n')
        date_times, users, messages = [], [], []

        for line in lines:
            # Extract date, time, user, and message
            match = re.match(r'(\d{2}/\d{2}/\d{2}), (\d{2}:\d{2}\s[ap]m) - (.*)', line)
            if match:
                date_times.append(f"{match.group(1)}, {match.group(2)}")
                message = match.group(3)
                processed_message_match = re.match(r'([^:]+):\s(.*)', message)
                if processed_message_match:
                    users.append(processed_message_match.group(1))
                    messages.append(processed_message_match.group(2))
                else:
                    users.append("System")
                    messages.append(message)

        # Convert lists into DataFrame
        df = pd.DataFrame({'date': date_times, 'user': users, 'message': messages})
        df['date'] = pd.to_datetime(df['date'], format='%d/%m/%y, %I:%M %p')
        df = df[df['message'] != '<Media omitted>']

    # Add additional time-based columns
    df['only_date'] = df['date'].dt.date
    df['year'] = df['date'].dt.year
    df['month_num'] = df['date'].dt.month
    df['month'] = df['date'].dt.month_name()
    df['day'] = df['date'].dt.day
    df['day_name'] = df['date'].dt.day_name()
    df['hour'] = df['date'].dt.hour
    df['minute'] = df['date'].dt.minute

    # Add period column
    df = add_period_column(df)

    return df
