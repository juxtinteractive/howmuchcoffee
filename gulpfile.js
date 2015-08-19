/* global process */
'use strict';
require('dotenv').load();
var fs = require('fs');
var gulp = require('gulp');

var bower = require('gulp-bower');
var browserify = require('gulp-browserify');
var plumber = require('gulp-plumber');
var sourcemaps = require('gulp-sourcemaps');
var sass = require('gulp-sass');
var replace = require('gulp-replace');

gulp.task('compile-js', function() {
  return gulp.src('client/src/js/main.js', {read:false})
  .pipe(plumber())
  .pipe(browserify({
    debug: true,
    paths: ['client/src/js', 'node_modules'],
    transform: ['debowerify']
  }))
  .pipe(replace(/%%PUBLIC_ADDRESS%%/g, process.env.PUBLIC_ADDRESS))
  .pipe(sourcemaps.init({loadMaps: true}))
  .pipe(sourcemaps.write('./'))
  .pipe(gulp.dest('client/build/_assets/js/'));
});

gulp.task('compile-sass', function() {
  return gulp.src('client/src/scss/main.scss')
  .pipe(plumber())
  .pipe(sass({
          sourceComments: 'map',
          sourcemap: true,
          errLogToConsole: true,
          cacheLocation: 'client/src/sass/.sass-cache'//,
          // includePaths: ['client/src/sass/']
        }))
  // .on('error', gutil.log)
  .pipe(sourcemaps.init({loadMaps: true}))
  .pipe(sourcemaps.write('./'))
  .pipe(gulp.dest('client/build/_assets/css'));
});

gulp.task('watch', function() {
  gulp.watch('client/src/**/*.js', ['compile-js']);
  gulp.watch('client/src/**/*.scss', ['compile-sass']);
});

gulp.task('default', ['watch']);
gulp.task('build', ['compile-js', 'compile-sass']);
