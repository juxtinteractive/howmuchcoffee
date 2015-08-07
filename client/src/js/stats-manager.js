'use strict';

var moment = require('moment');

function StatsManager() {
  this.data = [];
}

StatsManager.prototype.updateStats = function updateStats(newData) {
  this.data = newData;
};

function sumWithCondition(data, condition) {

  if(typeof condition === 'undefined') { condition = function() { return true; } }

  var _lastLevel = -1;
  var _summer = 0;
  for(var i = 0; i < data.length; i++) {
    var _sample = data[i];
    if(!condition(_sample)) { continue; }
    if(_sample[1] === 'empty' || _sample[1] === 'cups') {
      var _cups = _sample[1] === 'empty' ? 0 : _sample[2];
      if(_lastLevel === -1) {
        _lastLevel = _cups;
        continue;
      }

      if(_lastLevel > _cups) {
        _summer += _lastLevel - _cups;
      }
      _lastLevel = _cups;
    }
  }
  return _summer;
};

StatsManager.prototype.getCupsDrank = function getCupsDrank() {
  return sumWithCondition(this.data);
};

StatsManager.prototype.getFlushes = function getFlushes() {
  var testTime = moment(new Date()).subtract(40, 'minutes');
  return sumWithCondition(this.data, function(sample) {
    return sample[0].isBefore(testTime);
  }) * 0.75;
};


StatsManager.prototype.getProductivity = function getProductivity() {
  return this.getCupsDrank() * 0.5;
};

StatsManager.prototype.getPotLevel = function getPotLevel() {
  var _currentSample = this.data[this.data.length - 1];
  if(_currentSample[1] === 'empty') {
    return 0.0;
  } else if(_currentSample[1] === 'cups') {
    return _currentSample[2]
  } else {
    return -1;
  }
};


module.exports = StatsManager;
