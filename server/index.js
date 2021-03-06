require('dotenv').load();

var express = require('express');
var morgan = require('morgan')
var app = express();
app.use(morgan('combined'));
app.use(express.static(__dirname + '/../client/static'));
app.use(express.static(__dirname + '/../client/build'));
app.use(function(req, res, next) {
  res.sendFile('client/static/index.html', {root: __dirname + '/../'});
});
var port = parseInt(process.env.SERVER_PORT) || 8080;
var server = app.listen(port, function() {
  var host = server.address().address;
  var port = server.address().port;
  console.log('App listening at http://%s:%s', host, port);
});
