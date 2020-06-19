/* globals Chart:false, feather:false */

(function () {
  'use strict'

  feather.replace()
}())

$(document).ready(function() {
  $('a.active').removeClass('active');
  $('a[href="' + location.pathname + '"]').closest('a').addClass('active');
});