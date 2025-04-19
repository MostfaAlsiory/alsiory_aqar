document.addEventListener('DOMContentLoaded', function () {
    // تحديث قائمة المدن عند اختيار منطقة
    document.getElementById('region_id').addEventListener('change', function () {
        const regionId = this.value;
        const citySelect = document.getElementById('city_id');

        if (regionId) {
            fetch(`/api/cities?region_id=${regionId}`)
                .then(response => response.json())
                .then(data => {
                    citySelect.innerHTML = '<option value="">اختر المدينة...</option>';
                    data.forEach(city => {
                        citySelect.innerHTML += `<option value="${city.id}">${city.name}</option>`;
                    });
                });
        } else {
            citySelect.innerHTML = '<option value="">اختر المدينة...</option>';
            document.getElementById('district_id').innerHTML = '<option value="">اختر الحي...</option>';
        }
    });

    // تحديث قائمة الأحياء عند اختيار مدينة
    document.getElementById('city_id').addEventListener('change', function () {
        const cityId = this.value;
        const districtSelect = document.getElementById('district_id');

        if (cityId) {
            fetch(`/api/districts?city_id=${cityId}`)
                .then(response => response.json())
                .then(data => {
                    districtSelect.innerHTML = '<option value="">اختر الحي...</option>';
                    data.forEach(district => {
                        districtSelect.innerHTML += `<option value="${district.id}">${district.name}</option>`;
                    });
                });
        } else {
            districtSelect.innerHTML = '<option value="">اختر الحي...</option>';
        }
    });
});