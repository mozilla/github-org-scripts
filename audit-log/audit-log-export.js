/**
 * Run this code in the JS console on github's audit log page.
 * Example URL: https://github.com/orgs/acmecorp/audit-log
 */
var logs = [];

var lines = document.querySelectorAll('.audit-log-item');
for (var line of lines) {
  var data = {
    who: line.querySelector('.member-username').textContent,
//    app: line.querySelector('.audit-action-info > .context').textContent,
    what: line.querySelector('.audit-action-info').textContent.trim(),
    type: line.querySelector('.audit-type').textContent.trim(),
    when: line.querySelector('time').getAttribute('datetime')
  }
  logs.push(data);
}

var blob = new Blob([JSON.stringify(logs, null, 2)], {type: 'application/json'});
var url = window.URL.createObjectURL(blob);
var a = document.createElement('a');
a.setAttribute('href', url);
a.setAttribute('download', 'audit-log.json');
document.body.appendChild(a);
a.click();
