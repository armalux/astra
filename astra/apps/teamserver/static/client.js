function AstraClient(url) {
    var client = this;

    this.socket = new WebSocket(url);

    this.socket.onopen = function() {
        client.hello('astra');
    };

    this.socket.onmessage = function(evt) {
        client.onmessage(evt.data);

        var data = JSON.parse(evt.data);
        console.log(data);
        switch(data.msg_type) {
            case 'welcome':
                client.session_id = data.session_id;
                client.onopen();
                break;

            case 'subscribed':
                var request = client.pending_requests[data.request_id];
                delete client.pending_requests[data.request_id];
                client.subscriptions[request.topic] = data.subscription_id;
                break;

            case 'unsubscribed':
                var request = client.pending_requests[data.request_id];
                delete client.pending_requests[data.request_id];
                break;

            case 'published':
                var request = client.pending_requests[data.request_id];
                delete client.pending_requests[data.request_id];
                break;

            case 'event':
                break;

            case 'error':
                var request = client.pending_requests[data.request_id];
                delete client.pending_requests[data.request_id];
                console.error(data);
                break;

            case 'abort':
                alert('Session establishment failed: ' + data.details.message);
                break;
        }
    };

    this.subscriptions = {};
    client.pending_requests = {};

    this.onopen = function() {};
    this.onmessage = function(data) {};

    this.next_request_id = 0;
}

AstraClient.prototype.getRequestId = function() {
    return this.next_request_id++;
};

AstraClient.prototype.subscribe = function(topic) {
    var msg = {
        'msg_type': 'subscribe',
        'request_id': this.getRequestId(),
        'options': {},
        'topic': topic
    };

    this.pending_requests[msg['request_id']] = msg;
    this.socket.send(JSON.stringify(msg));
};

AstraClient.prototype.hello = function() {
    var msg = {
        'msg_type': 'hello'
    };

    this.socket.send(JSON.stringify(msg));
};

AstraClient.prototype.publish = function(topic, options, args, kwargs) {
    if(args == undefined)
        args = [];

    if(kwargs == undefined)
        kwargs = {};

    var msg = {
        'msg_type': 'publish',
        'request_id': this.getRequestId(),
        'options': options,
        'topic': topic,
        'args': args,
        'kwargs': kwargs
    };

    this.pending_requests[msg['request_id']] = msg;
    this.socket.send(JSON.stringify(msg));
};

AstraClient.prototype.call = function(func_name, args, kwargs) {
    var msg = {
        'msg_type': 'call',
        'function': func_name,
        'args': args,
        'kwargs': kwargs
    };

    this.pending_requests[msg['request_id']] = msg;
    this.socket.send(JSON.stringify(msg));
};
