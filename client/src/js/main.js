'use strict';

var $ = require('jquery');
var papa = require('papaparse');
var moment = require('moment');
var StatsManager = require('./stats-manager');

$(function() {
  function pullData() {
    papa.parse('%%PUBLIC_ADDRESS%%', {
      download: true,
      complete: parseResultsTable,
      error: function() {
        setTimeout(pullData, 10 * 1000);
      }
    });
  }

  var statsMan = new StatsManager();
  function parseResultsTable(results) {
    var filtered = results.data.map(function(row) {
      if(row.length < 3) { return null; }
      row[0] = moment(row[0]);
      return row;
    });
    var now = new Date();
    var today = moment([now.getFullYear(), now.getMonth(), now.getDate()]);
    filtered = filtered.reduce(function(m, v) {
      if(v === null) { return m; }
      var diffFromMidnight = v[0].diff(today, 'days', true);
      if(diffFromMidnight < 1 && diffFromMidnight > 0) {
        m.push(v);
      }
      return m;
    }, []);

    filtered.sort(function(a, b) { return a[0].diff(b[0]); });

    statsMan.updateStats(filtered);
    updateDisplay();
  }
  function updateDisplay() {
    console.log(statsMan.getPotLevel(), statsMan.getCupsDrank(), statsMan.getFlushes(), statsMan.getProductivity());
    var _cups = Math.round(statsMan.getCupsDrank());
    var _pots = Math.min(3, Math.floor(_cups / 12));
    $('.coffee-tile .caffeine .number').text(Math.ceil((_cups * 0.15) * 10) / 10);
    $('.coffee-tile .flush .number').text(Math.ceil(statsMan.getFlushes()));
    $('.coffee-tile .productivity .number').text(Math.ceil(_cups * 0.5));
    $('.coffee-tile .cups-grid .cup').show();
    $('.coffee-tile .cups-grid .cup').slice(-(12 - (_cups % 12)) % 12).hide();
    $('.coffee-tile .pots-grid .pot').show();
    $('.coffee-tile .pots-grid .pot').slice(-(3 - (_pots % 3)) % 3).hide();
    var _metterLevel = Math.min(4, Math.floor(_cups / 12));

    $('.coffee-tile .word-meter .arrow').css('top', (20 * (5 - _metterLevel - 1) + 10) + '%');

    $('.coffee-tile .pot-view .level').css('height', ((65 - 11) * Math.min(1.0, (statsMan.getPotLevel() / 12)) + 11) + '%');
    setTimeout(pullData, 10 * 1000);
  }
  pullData();
});
