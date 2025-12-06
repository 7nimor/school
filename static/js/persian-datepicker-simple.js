// تقویم شمسی ساده
class PersianDatePicker {
    constructor(inputId, options = {}) {
        this.input = document.getElementById(inputId);
        this.options = {
            minYear: options.minYear || 1390,
            maxYear: options.maxYear || 1410,
            onChange: options.onChange || null,
            ...options
        };
        
        this.persianMonths = [
            "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
            "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
        ];
        
        this.persianWeekDays = ["ش", "ی", "د", "س", "چ", "پ", "ج"];
        
        this.isOpen = false;
        this.pickerContainer = null;
        
        this.init();
    }
    
    init() {
        if (!this.input) return;
        
        // ایجاد تقویم
        this.createPicker();
        
        // رویداد کلیک روی input
        this.input.addEventListener('click', (e) => {
            e.preventDefault();
            this.togglePicker();
        });
        
        // مقدار اولیه
        if (this.input.value) {
            this.setValue(this.input.value);
        } else {
            this.setToday();
        }
    }
    
    setToday() {
        const today = new Date();
        const persian = this.gregorianToPersian(today.getFullYear(), today.getMonth() + 1, today.getDate());
        this.selectedYear = persian.year;
        this.selectedMonth = persian.month - 1;
        this.selectedDay = persian.day;
        this.updateInput();
    }
    
    // تبدیل تاریخ میلادی به شمسی
    gregorianToPersian(gy, gm, gd) {
        var g_d_m, jy, jm, jd, gy2, days;
        g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334];
        gy2 = (gm > 2) ? (gy + 1) : gy;
        days = 355666 + (365 * gy) + ~~((gy2 + 3) / 4) - ~~((gy2 + 99) / 100) + ~~((gy2 + 399) / 400) + gd + g_d_m[gm - 1];
        jy = -1595 + (33 * ~~(days / 12053));
        days %= 12053;
        jy += 4 * ~~(days / 1461);
        days %= 1461;
        if (days > 365) {
            jy += ~~((days - 1) / 365);
            days = (days - 1) % 365;
        }
        if (days < 186) {
            jm = 1 + ~~(days / 31);
            jd = 1 + (days % 31);
        } else {
            jm = 7 + ~~((days - 186) / 30);
            jd = 1 + ((days - 186) % 30);
        }
        return { year: jy, month: jm, day: jd };
    }
    
    setValue(value) {
        // اگر تاریخ میلادی است، به شمسی تبدیل کن
        if (value.match(/^\d{4}-\d{2}-\d{2}$/)) {
            const parts = value.split('-');
            const persian = this.gregorianToPersian(parseInt(parts[0]), parseInt(parts[1]), parseInt(parts[2]));
            this.selectedYear = persian.year;
            this.selectedMonth = persian.month - 1;
            this.selectedDay = persian.day;
        } else if (value.match(/^\d{4}\/\d{2}\/\d{2}$/)) {
            // اگر تاریخ شمسی است
            const parts = value.split('/');
            this.selectedYear = parseInt(parts[0]);
            this.selectedMonth = parseInt(parts[1]) - 1;
            this.selectedDay = parseInt(parts[2]);
        }
        this.updateInput();
    }
    
    updateInput() {
        const monthName = this.persianMonths[this.selectedMonth];
        this.input.value = `${this.selectedDay} / ${monthName} / ${this.selectedYear}`;
        
        // تبدیل به میلادی برای hidden input
        this.updateGregorian();
    }
    
    updateGregorian() {
        try {
            // تبدیل شمسی به میلادی با استفاده از الگوریتم دقیق
            const gregorianDate = this.persianToGregorian(this.selectedYear, this.selectedMonth + 1, this.selectedDay);
            
            // اگر hidden input وجود دارد، به‌روزرسانی کن
            // ابتدا سعی کن با id + '-hidden' پیدا کن
            let hiddenInput = document.getElementById(this.input.id + '-hidden');
            // اگر پیدا نشد، سعی کن با id + '-alt' پیدا کن
            if (!hiddenInput) {
                hiddenInput = document.getElementById(this.input.id + '-alt');
            }
            // اگر هنوز پیدا نشد، سعی کن با name='date' پیدا کن
            if (!hiddenInput) {
                hiddenInput = document.querySelector('input[name="date"][type="hidden"]');
            }
            if (hiddenInput) {
                hiddenInput.value = gregorianDate;
                console.log('تاریخ میلادی در updateGregorian تنظیم شد:', gregorianDate, 'برای فیلد:', hiddenInput.id || hiddenInput.name);
            } else {
                console.warn('فیلد hidden برای تاریخ پیدا نشد. ID input:', this.input.id);
            }
            
            // فراخوانی callback
            if (this.options.onChange) {
                this.options.onChange(gregorianDate);
            }
            
            return gregorianDate;
        } catch(e) {
            console.error('خطا در تبدیل تاریخ:', e);
            return null;
        }
    }
    
    // تبدیل تاریخ شمسی به میلادی
    persianToGregorian(jy, jm, jd) {
        var sal_a, gy, gm, gd, days;
        jy += 1595;
        days = -355668 + (365 * jy) + (~~(jy / 33) * 8) + ~~(((jy % 33) + 3) / 4) + jd + ((jm < 7) ? (jm - 1) * 31 : ((jm - 7) * 30) + 186);
        gy = 400 * ~~(days / 146097);
        days %= 146097;
        if (days > 36524) {
            gy += 100 * ~~(--days / 36524);
            days %= 36524;
            if (days >= 365) days++;
        }
        gy += 4 * ~~(days / 1461);
        days %= 1461;
        if (days > 365) {
            gy += ~~((days - 1) / 365);
            days = (days - 1) % 365;
        }
        gd = days + 1;
        sal_a = [0, 31, ((gy % 4 === 0 && gy % 100 !== 0) || (gy % 400 === 0)) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
        for (gm = 0; gm < 13 && gd > sal_a[gm]; gm++) gd -= sal_a[gm];
        return gy + '-' + String(gm).padStart(2, '0') + '-' + String(gd).padStart(2, '0');
    }
    
    createPicker() {
        // ایجاد container برای picker
        this.pickerContainer = document.createElement('div');
        this.pickerContainer.className = 'persian-datepicker-container';
        this.pickerContainer.style.cssText = `
            position: absolute;
            z-index: 1000;
            background: white;
            border: 2px solid #1e3c72;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            display: none;
            margin-top: 5px;
            width: 300px;
            font-family: 'IranYekan', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        `;
        
        // ایجاد سه ستون برای روز، ماه، سال
        const columns = [
            { label: 'روز', type: 'day' },
            { label: 'ماه', type: 'month' },
            { label: 'سال', type: 'year' }
        ];
        
        columns.forEach((col, index) => {
            const column = document.createElement('div');
            column.className = 'picker-column';
            column.style.cssText = `
                flex: 1;
                max-height: 250px;
                overflow-y: auto;
                border-left: ${index > 0 ? '1px solid #ddd' : 'none'};
            `;
            
            const label = document.createElement('div');
            label.textContent = col.label;
            label.style.cssText = `
                background: #1e3c72;
                color: white;
                padding: 10px;
                text-align: center;
                font-weight: bold;
                position: sticky;
                top: 0;
                z-index: 10;
            `;
            column.appendChild(label);
            
            const list = document.createElement('ul');
            list.style.cssText = `
                list-style: none;
                padding: 0;
                margin: 0;
                text-align: center;
            `;
            
            let options = [];
            if (col.type === 'day') {
                const daysInMonth = this.getDaysInMonth(this.selectedYear, this.selectedMonth + 1);
                options = Array.from({ length: daysInMonth }, (_, i) => i + 1);
            } else if (col.type === 'month') {
                options = this.persianMonths;
            } else {
                options = Array.from(
                    { length: this.options.maxYear - this.options.minYear + 1 },
                    (_, i) => this.options.minYear + i
                );
            }
            
            options.forEach((opt, idx) => {
                const li = document.createElement('li');
                const value = col.type === 'month' ? idx : opt;
                const isSelected = 
                    (col.type === 'day' && opt === this.selectedDay) ||
                    (col.type === 'month' && idx === this.selectedMonth) ||
                    (col.type === 'year' && opt === this.selectedYear);
                
                li.textContent = col.type === 'month' ? opt : opt;
                li.style.cssText = `
                    padding: 12px;
                    cursor: pointer;
                    transition: all 0.2s;
                    ${isSelected ? 'background: #1e3c72; color: white; font-weight: bold;' : ''}
                `;
                
                li.addEventListener('mouseenter', () => {
                    if (!isSelected) {
                        li.style.background = '#f0f0f0';
                    }
                });
                
                li.addEventListener('mouseleave', () => {
                    if (!isSelected) {
                        li.style.background = '';
                    }
                });
                
                li.addEventListener('click', () => {
                    if (col.type === 'day') {
                        this.selectedDay = opt;
                    } else if (col.type === 'month') {
                        this.selectedMonth = idx;
                        // بررسی تعداد روزهای ماه جدید
                        const newDaysInMonth = this.getDaysInMonth(this.selectedYear, this.selectedMonth + 1);
                        if (this.selectedDay > newDaysInMonth) {
                            this.selectedDay = newDaysInMonth;
                        }
                    } else {
                        this.selectedYear = opt;
                        // بررسی تعداد روزهای ماه جدید
                        const newDaysInMonth = this.getDaysInMonth(this.selectedYear, this.selectedMonth + 1);
                        if (this.selectedDay > newDaysInMonth) {
                            this.selectedDay = newDaysInMonth;
                        }
                    }
                    this.updateInput();
                    this.renderPicker();
                });
                
                list.appendChild(li);
            });
            
            column.appendChild(list);
            this.pickerContainer.appendChild(column);
        });
        
        // اضافه کردن به body
        document.body.appendChild(this.pickerContainer);
        
        // تنظیم موقعیت
        this.updatePosition();
    }
    
    getDaysInMonth(year, month) {
        // تعداد روزهای ماه‌های شمسی
        // ماه‌های 1 تا 6: 31 روز
        // ماه‌های 7 تا 11: 30 روز
        // ماه 12 (اسفند): 29 روز (در سال کبیسه 30 روز)
        if (month <= 6) return 31;
        if (month <= 11) return 30;
        // اسفند - بررسی سال کبیسه شمسی
        return this.isPersianLeapYear(year) ? 30 : 29;
    }
    
    // بررسی سال کبیسه شمسی
    isPersianLeapYear(year) {
        const breaks = [1, 5, 9, 13, 17, 22, 26, 30];
        const cycle = year % 33;
        return breaks.includes(cycle);
    }
    
    renderPicker() {
        if (!this.pickerContainer) return;
        
        const columns = this.pickerContainer.querySelectorAll('.picker-column');
        columns.forEach((column, colIndex) => {
            const list = column.querySelector('ul');
            list.innerHTML = '';
            
            let options = [];
            if (colIndex === 0) {
                const daysInMonth = this.getDaysInMonth(this.selectedYear, this.selectedMonth + 1);
                options = Array.from({ length: daysInMonth }, (_, i) => i + 1);
            } else if (colIndex === 1) {
                options = this.persianMonths;
            } else {
                options = Array.from(
                    { length: this.options.maxYear - this.options.minYear + 1 },
                    (_, i) => this.options.minYear + i
                );
            }
            
            options.forEach((opt, idx) => {
                const li = document.createElement('li');
                const value = colIndex === 1 ? idx : opt;
                const isSelected = 
                    (colIndex === 0 && opt === this.selectedDay) ||
                    (colIndex === 1 && idx === this.selectedMonth) ||
                    (colIndex === 2 && opt === this.selectedYear);
                
                li.textContent = colIndex === 1 ? opt : opt;
                li.style.cssText = `
                    padding: 12px;
                    cursor: pointer;
                    transition: all 0.2s;
                    ${isSelected ? 'background: #1e3c72; color: white; font-weight: bold;' : ''}
                `;
                
                li.addEventListener('mouseenter', () => {
                    if (!isSelected) {
                        li.style.background = '#f0f0f0';
                    }
                });
                
                li.addEventListener('mouseleave', () => {
                    if (!isSelected) {
                        li.style.background = '';
                    }
                });
                
                li.addEventListener('click', () => {
                    if (colIndex === 0) {
                        this.selectedDay = opt;
                    } else if (colIndex === 1) {
                        this.selectedMonth = idx;
                        const newDaysInMonth = this.getDaysInMonth(this.selectedYear, this.selectedMonth + 1);
                        if (this.selectedDay > newDaysInMonth) {
                            this.selectedDay = newDaysInMonth;
                        }
                    } else {
                        this.selectedYear = opt;
                        const newDaysInMonth = this.getDaysInMonth(this.selectedYear, this.selectedMonth + 1);
                        if (this.selectedDay > newDaysInMonth) {
                            this.selectedDay = newDaysInMonth;
                        }
                    }
                    this.updateInput();
                    this.renderPicker();
                });
                
                list.appendChild(li);
            });
        });
    }
    
    updatePosition() {
        if (!this.pickerContainer || !this.input) return;
        
        const rect = this.input.getBoundingClientRect();
        this.pickerContainer.style.left = rect.left + 'px';
        this.pickerContainer.style.top = (rect.bottom + window.scrollY + 5) + 'px';
    }
    
    togglePicker() {
        this.isOpen = !this.isOpen;
        
        if (this.isOpen) {
            this.updatePosition();
            this.renderPicker();
            this.pickerContainer.style.display = 'flex';
            
            // بستن با کلیک خارج
            setTimeout(() => {
                document.addEventListener('click', this.handleClickOutside.bind(this), true);
            }, 0);
        } else {
            this.pickerContainer.style.display = 'none';
            document.removeEventListener('click', this.handleClickOutside.bind(this), true);
        }
    }
    
    handleClickOutside(e) {
        if (!this.pickerContainer.contains(e.target) && !this.input.contains(e.target)) {
            this.isOpen = false;
            this.pickerContainer.style.display = 'none';
            document.removeEventListener('click', this.handleClickOutside.bind(this), true);
        }
    }
}

// تابع ساده برای استفاده
function initPersianDatePicker(inputId, options = {}) {
    return new PersianDatePicker(inputId, options);
}

