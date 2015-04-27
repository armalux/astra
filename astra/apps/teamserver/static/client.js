function AstraClient(url) {
    this.socket = new WebSocket(url);
    this.socket.onmessage = function(evt) {
        console.log(JSON.parse(evt.data));
    };
}

AstraClient.prototype.subscribe = function(channel) {
    var msg = {
        'type': 'subscribe',
        'channel': channel
    };

    this.socket.send(JSON.stringify(msg));
};

AstraClient.prototype.publish = function(channel, message) {
    var msg = {
        'type': 'publish',
        'channel': channel,
        'message': message
    };

    this.socket.send(JSON.stringify(msg));
};
