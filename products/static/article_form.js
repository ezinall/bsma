$(document).ready(function () {
    if ($("#id_product").val() !== '') {
        $("#product_code").prop('disabled', false).removeClass("btn-outline-secondary").addClass("btn-success");
    }
})

$("#id_product").change(function () {
    if ($("#id_product").val() !== '') {
        $("#product_code").prop('disabled', false).removeClass("btn-outline-secondary").addClass("btn-success");
        $("#id_serial").val("").prop('readonly', false)
        $("#id_imei").val("").prop('readonly', false)
        $("#id_mac").val("").prop('readonly', false)
    } else {
        $("#product_code").prop('disabled', true).removeClass("btn-success").addClass("btn-outline-secondary");
    }
});

function getCode() {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', `/articles/next?product=${$("#id_product").val()}`, false);
    xhr.send();

    if (xhr.status !== 200) {
        // обработать ошибку
        alert(xhr.status + ': ' + xhr.statusText); // пример вывода: 404: Not Found
    } else {
        // вывести результат
        // console.log(xhr.responseText); // responseText -- текст ответа.
        var obj = JSON.parse(xhr.responseText);
        $("#id_serial").val(obj.serial).prop('readonly', true)
        $("#id_imei").val(obj.imei).prop('readonly', true)
        $("#id_mac").val(obj.mac).prop('readonly', true)

    }
}