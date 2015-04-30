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

            case 'event':
                if(client.event_handlers[data.topic] == undefined)
                    break;

                for(var i=0 ; i < client.event_handlers[data.topic].length ; i++)
                {
                    client.event_handlers[data.topic][i](data);
                }

                break;

            case 'invoke':
                if(client.registrations[data.procedure] == undefined)
                {
                    var msg = {
                        'type': 'exceptions',
                        'invoke_id': data.invoke_id,
                        'message': 'No such procedure.'
                    };

                    client.socket.send(JSON.stringify(msg));
                    break;
                }

                var result = client.registrations[data.procedure](args, kwargs);
                if(result == undefined)
                    result = {};

                var msg = {
                    'type': 'yield',
                    'invoke_id': data.invoke_id,
                    'result': result
                };

                client.socket.send(JSON.stringify(msg));
                break;

            case 'result':
                if(client.pending_calls[data.request_id] == undefined)
                    break;

                client.pending_calls[data.request_id](data.result);
                break;

            case 'error':
                console.error('Request FAILED: ' + JSON.stringify(request));
                break;

            case 'success':
                console.debug('Request successful: ' + JSON.stringify(request));
                break;
        }
    };

    this.subscriptions = [];
    this.registrations = {};

    this.pending_requests = {};
    this.pending_calls = {};

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

AstraClient.prototype.publish = function(topic, args, kwargs) {
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

AstraClient.prototype.register = function(func_name, callback) {
    if(this.registrations[func_name] != undefined)
        return false;

    var msg = {
        'type': 'register',
        'request_id': this.getRequestId(),
        'procedure': func_name,
    };

    this.pending_requests[msg['request_id']] = msg;
    this.registrations[func_name] = callback;
    this.socket.send(JSON.stringify(msg));
};

AstraClient.prototype.call = function(func_name, args, kwargs, callback) {
    var msg = {
        'type': 'call',
        'request_id': this.getRequestId(),
        'procedure': func_name,
        'args': args,
        'kwargs': kwargs
    };

    this.pending_calls[msg['request_id']] = callback;
    this.pending_requests[msg['request_id']] = msg;
    this.socket.send(JSON.stringify(msg));
};
