# 🎨 Extent Report-Style Customization Guide

## Overview

This pytest-html report has been **heavily customized** to mimic the look and feel of **Extent Reports** (popular in Selenium automation). The customization provides a professional, modern, and interactive test report.

---

## 🌟 Key Features (Extent Report Style)

### 1. **Modern Gradient Theme**
- Beautiful purple-to-blue gradient headers (similar to Extent Reports)
- Consistent color scheme throughout the report
- Professional card-based layout with shadows and depth

### 2. **All Screenshots Visible at Once**
- **No carousel/slider** - all 8 screenshots displayed vertically
- **Step numbering** - Automatic "Step 1:", "Step 2:", etc.
- **Full-width images** - No cropping or half-images
- **Gradient headers** for each screenshot with icons

### 3. **Interactive Elements**
- **Click-to-zoom** - Click any screenshot to zoom in/out
- **Hover effects** - Images scale slightly on hover
- **Smooth transitions** - Professional animations
- **Responsive design** - Works on all screen sizes

### 4. **Professional Styling**
- Status badges with color coding (Green/Red/Orange)
- Modern typography (Segoe UI font)
- Card-based sections with rounded corners
- Box shadows for depth
- Gradient accents throughout

---

## 🎨 Color Scheme (Customizable)

The report uses CSS variables for easy customization:

```css
:root {
    --primary-color: #667eea;      /* Purple */
    --secondary-color: #764ba2;    /* Dark Purple */
    --success-color: #4CAF50;      /* Green */
    --danger-color: #f44336;       /* Red */
    --warning-color: #ff9800;      /* Orange */
    --info-color: #2196F3;         /* Blue */
}
```

### To Change Colors:
1. Open `conftest.py`
2. Find the `:root` section in the CSS
3. Modify the color values (use hex codes or RGB)
4. Re-run your test to generate a new report

---

## 📐 Report Sections (Extent-Style Layout)

### 1. **Header Section**
- Large gradient background
- Test suite title
- Professional padding and shadows

### 2. **Summary Section**
- Custom summary box with gradient
- Test execution overview
- Quick statistics

### 3. **Environment/Metadata**
- System information table
- Python version, packages, etc.
- Styled with hover effects

### 4. **Test Results Table**
- Gradient header row
- Status badges (Passed/Failed/Skipped)
- Hover effects on rows
- Organized columns

### 5. **Screenshots Section**
- **Step-by-step visual documentation**
- Automatic numbering (Step 1, Step 2, etc.)
- Gradient headers with emoji indicators 📸
- Full-width images with borders
- Click-to-zoom functionality
- Hover scale effects

---

## 🔧 Advanced Customization Options

### 1. **Change the Gradient Colors**

In `conftest.py`, find and modify:

```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

Replace `#667eea` and `#764ba2` with your preferred colors.

### 2. **Add Company Logo**

Add this to the `pytest_html_report_summary` function in `conftest.py`:

```python
def pytest_html_report_summary(summary):
    summary.extend([
        '<div style="text-align: center; padding: 20px;">',
        '<img src="data:image/png;base64,YOUR_BASE64_LOGO_HERE" style="max-width: 200px;">',
        '</div>',
        # ... rest of summary ...
    ])
```

### 3. **Modify Screenshot Border Colors**

In the CSS section, find:

```css
.media-container img {
    border: 3px solid var(--success-color) !important;
}
```

Change `var(--success-color)` to any color you want (e.g., `#2196F3` for blue).

### 4. **Change Font Family**

Find in CSS:

```css
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
```

Replace with your preferred font.

### 5. **Adjust Screenshot Sizes**

Modify in CSS:

```css
.media-container img {
    max-width: 100% !important;  /* Change to 80%, 90%, etc. */
}
```

---

## 🖼️ Screenshot Customization

### Current Screenshot Features:
- ✅ Full-width display (no cropping)
- ✅ Automatic step numbering
- ✅ Gradient headers with labels
- ✅ Click-to-zoom functionality
- ✅ Hover scale effect
- ✅ Green borders with shadows
- ✅ Rounded corners
- ✅ Print-friendly layout

### To Customize Screenshot Display:

**Change Border Style:**
```css
.media-container img {
    border: 3px solid #4CAF50 !important;  /* Modify thickness and color */
    border-radius: 8px !important;          /* Modify corner roundness */
}
```

**Modify Header Style:**
```css
.media-container::before {
    background: linear-gradient(135deg, #2196F3 0%, #667eea 100%);  /* New colors */
    font-size: 18px;                                                 /* New size */
    padding: 15px 25px;                                             /* New padding */
}
```

**Adjust Spacing:**
```css
.media-container {
    margin: 30px 0 !important;  /* Increase/decrease spacing between screenshots */
}
```

---

## 📱 Responsive Design

The report automatically adapts to different screen sizes:

- **Desktop**: Full-width screenshots with all features
- **Tablet**: Optimized layout with adjusted spacing
- **Mobile**: Stacked layout, touch-friendly zoom
- **Print**: Optimized for PDF export and printing

---

## 🖨️ Print Customization

When printing the report (or saving as PDF):

```css
@media print {
    .media-container {
        page-break-inside: avoid;  /* Prevents screenshots from splitting across pages */
    }
    
    .media-container img {
        max-width: 100%;
        border: 1px solid #000;    /* Black border for print */
    }
}
```

---

## 🚀 Quick Customization Examples

### Example 1: Blue Theme
```css
:root {
    --primary-color: #2196F3;
    --secondary-color: #1976D2;
}
```

### Example 2: Red Theme
```css
:root {
    --primary-color: #f44336;
    --secondary-color: #d32f2f;
}
```

### Example 3: Green Theme
```css
:root {
    --primary-color: #4CAF50;
    --secondary-color: #388E3C;
}
```

---

## 📦 What's Different from Standard pytest-html?

| Feature | Standard pytest-html | Our Customization |
|---------|---------------------|-------------------|
| **Screenshot Display** | Carousel (1 at a time) | All visible, stacked vertically |
| **Styling** | Basic HTML table | Extent Report-style with gradients |
| **Colors** | Plain | Professional gradient theme |
| **Interactions** | None | Click-to-zoom, hover effects |
| **Step Numbers** | No | Automatic numbering |
| **Responsive** | Limited | Fully responsive |
| **Print** | Basic | Optimized for PDF |

---

## 💡 Tips and Best Practices

1. **Keep conftest.py** - This file contains all customizations
2. **Test after changes** - Always run a test to verify your CSS changes
3. **Use CSS variables** - Makes global color changes easier
4. **Backup original** - Keep a copy before heavy customization
5. **Browser compatibility** - Test in Chrome, Firefox, Edge
6. **File size** - Monitor report size with many screenshots
7. **Screenshots quality** - Higher resolution = larger files

---

## 🔍 Troubleshooting

### Screenshots not appearing?
- Check that the test passed successfully
- Verify `conftest.py` is in the same directory as the test
- Ensure `capture_screenshot()` function is being called

### Styling not applied?
- Clear browser cache and refresh
- Re-run the test to generate a new report
- Check for CSS syntax errors in `conftest.py`

### Images still in carousel?
- The JavaScript should remove carousel controls
- Check browser console for JavaScript errors
- Ensure report was generated AFTER editing `conftest.py`

---

## 📚 Files Involved

- **conftest.py** - Contains all CSS and JavaScript customizations
- **TC_HappyFlow.py** - Main test file with screenshot capture
- **report.html** - Generated report (create new after changes)
- **README.md** - General documentation
- **CUSTOMIZATION_GUIDE.md** - This file

---

## 🎓 Learning Resources

To further customize your reports, learn about:
- CSS Flexbox and Grid
- CSS Gradients
- JavaScript DOM manipulation
- pytest-html hooks and API
- HTML5 and modern web design

---

## 📞 Need Help?

If you need assistance with customization:
1. Check the CSS comments in `conftest.py`
2. Review this guide
3. Test changes incrementally
4. Use browser developer tools (F12) to inspect elements

---

**Created by**: Automation Team  
**Version**: 1.0  
**Last Updated**: 2025  

---

**🎉 Enjoy your professional Extent Report-style pytest-html reports!**
