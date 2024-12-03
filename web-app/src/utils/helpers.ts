export const minifyMessageLength = (message: string, length: number = 50) => {
    if(message.length > length) {
        return message.substring(0, length) + "..."
    }
    return message;
}