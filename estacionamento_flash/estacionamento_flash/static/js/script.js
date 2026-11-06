document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll('input[name="placa"]').forEach((input) => {
    input.addEventListener("input", () => input.value = input.value.toUpperCase().replace(/[^A-Z0-9]/g, ""));
  });
  document.querySelectorAll('input[name="cpf"]').forEach((input) => {
    input.addEventListener("input", () => {
      let v = input.value.replace(/\D/g, "").slice(0, 11);
      v = v.replace(/(\d{3})(\d)/, "$1.$2").replace(/(\d{3})(\d)/, "$1.$2").replace(/(\d{3})(\d{1,2})$/, "$1-$2");
      input.value = v;
    });
  });
});