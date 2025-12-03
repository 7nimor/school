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
        const today = persianDatepicker.toPersian(new Date());
        if (today) {
            this.selectedYear = today.year;
            this.selectedMonth = today.month - 1;
            this.selectedDay = today.date;
            this.updateInput();
        }
    }
    
    setValue(value) {
        // اگر تاریخ میلادی است، به شمسی تبدیل کن
        if (value.match(/^\d{4}-\d{2}-\d{2}$/)) {
            const parts = value.split('-');
            const gregorianDate = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]));
            const persianDate = persianDatepicker.toPersian(gregorianDate);
            if (persianDate) {
                this.selectedYear = persianDate.year;
                this.selectedMonth = persianDate.month - 1;
                this.selectedDay = persianDate.date;
            }
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
            const pd = new persianDate([this.selectedYear, this.selectedMonth + 1, this.selectedDay]);
            const gregorian = pd.toCalendar('gregorian');
            const gYear = gregorian.year;
            const gMonth = String(gregorian.month).padStart(2, '0');
            const gDay = String(gregorian.date).padStart(2, '0');
            const gregorianDate = `${gYear}-${gMonth}-${gDay}`;
            
            // اگر hidden input وجود دارد، به‌روزرسانی کن
            const hiddenInput = document.getElementById(this.input.id + '-hidden');
            if (hiddenInput) {
                hiddenInput.value = gregorianDate;
            }
            
            // فراخوانی callback
            if (this.options.onChange) {
                this.options.onChange(gregorianDate);
            }
        } catch(e) {
            console.error('خطا در تبدیل تاریخ:', e);
        }
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
        try {
            const pd = new persianDate([year, month, 1]);
            return pd.daysInMonth();
        } catch(e) {
            return 30;
        }
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

