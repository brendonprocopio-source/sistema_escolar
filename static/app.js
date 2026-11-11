// Pequenos confortos de uso. O sistema funciona inteiro sem JavaScript.
document.addEventListener('click', function (e) {
  var b = e.target.closest('[data-menu]');
  if (b) { document.body.classList.toggle('menu'); return; }
  if (document.body.classList.contains('menu') && !e.target.closest('.side')) document.body.classList.remove('menu');
});
document.addEventListener('submit', function (e) {
  var msg = e.target.getAttribute('data-confirma');
  if (msg && !window.confirm(msg)) e.preventDefault();
});
// Nova matrícula: sugere o valor do curso ao escolher a turma.
var turma = document.querySelector('select[data-valores]');
if (turma) turma.addEventListener('change', function () {
  var v = turma.selectedOptions[0] && turma.selectedOptions[0].getAttribute('data-valor');
  var campo = document.querySelector('input[name=valor_total]');
  if (v && campo) campo.value = Number(v).toFixed(2);
});
// Chamada: marcar/desmarcar todos.
var todos = document.querySelector('[data-todos]');
if (todos) todos.addEventListener('click', function () {
  var caixas = document.querySelectorAll('input[type=checkbox][name^=p_]');
  var marcar = Array.prototype.some.call(caixas, function (c) { return !c.checked; });
  Array.prototype.forEach.call(caixas, function (c) { c.checked = marcar; });
});
