function AstraClient(url) {
    var client = this;

    this.socket = new WebSocket(url);

    this.socket.onopen = function() {
        client.hello();
    };

    this.socket.onmessage = function(evt) {
        client.onmessage(evt.data);

        var data = JSON.parse(evt.data);

        if(data.request_id != undefined)
        {
            var request = client.pending_requests[data.request_id];
            delete client.pending_requests[data.request_id];
        }

        switch(data.type) {
            case 'welcome':
                client.session_id = data.session_id;
                client.onopen();
                break;

            case 'subscribed':
                client.subscriptions.push(request.topic);
                break;

            case 'unsubscribed':
                break;

            case 'published':
                break;

            case 'event':
                if(client.event_handlers[data.topic] == undefined)
                    break;

                for(var i=0 ; i < client.event_handlers[data.topic].length ; i++)
                {
                    client.event_handlers[data.topic][i](data);
                }

                break;

            case 'error':
                console.error(data);
                break;

            case 'abort':
                alert('Session establishment failed: ' + data.details.message);
                break;
        }
    };

    this.subscriptions = [];
    client.pending_requests = {};

    this.onopen = function() {};
    this.onmessage = function(data) {};

    this.next_request_id = 0;

    this.event_handlers = {};
}

AstraClient.prototype.getRequestId = function() {
    return this.next_request_id++;
};

AstraClient.prototype.subscribed = function(topic) {
    for( var i=0 ; i < this.subscriptions.length ; i++ )
    {
        if(this.subscriptions[i] == topic)
            return true;
    }

    return false;
};

AstraClient.prototype.subscribe = function(topic, callback) {

    if(this.event_handlers[topic] == undefined)
        this.event_handlers[topic] = [];

    this.event_handlers[topic].push(callback);

    if(this.subscribed(topic))
        return;

    var msg = {
        'type': 'subscribe',
        'request_id': this.getRequestId(),
        'topic': topic
    };

    this.pending_requests[msg['request_id']] = msg;
    this.socket.send(JSON.stringify(msg));
};

AstraClient.prototype.hello = function() {
    var msg = {
        'type': 'hello'
    };

    this.socket.send(JSON.stringify(msg));
};

AstraClient.prototype.publish = function(topic, options, args, kwargs) {
    if(args == undefined)
        args = [];

    if(kwargs == undefined)
        kwargs = {};

    var msg = {
        'type': 'publish',
        'request_id': this.getRequestId(),
        'topic': topic,
        'args': args,
        'kwargs': kwargs
    };

    this.pending_requests[msg['request_id']] = msg;
    this.socket.send(JSON.stringify(msg));
};

AstraClient.prototype.call = function(func_name, args, kwargs) {
    var msg = {
        'type': 'call',
        'procedure': func_name,
        'args': args,
        'kwargs': kwargs
    };

    this.pending_requests[msg['request_id']] = msg;
    this.socket.send(JSON.stringify(msg));
};
