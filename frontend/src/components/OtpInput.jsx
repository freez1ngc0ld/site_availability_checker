import React from 'react';

export default function OtpInput({ value, onChange }) {
  const handleChange = (element, index) => {
    if (isNaN(element.value)) return false;

    let newOtp = [...value];
    newOtp[index] = element.value;
    onChange(newOtp);

    if (element.nextSibling && element.value !== "") {
      element.nextSibling.focus();
    }
  };

  const handleKeyDown = (e, index) => {
    if (e.key === "Backspace" && !value[index] && e.target.previousSibling) {
      e.target.previousSibling.focus();
    }
  };

  return (
    <div className="otp-container">
      {value.map((data, index) => (
        <input
          key={index}
          type="text"
          maxLength="1"
          className="input-field otp-box"
          value={data}
          onChange={(e) => handleChange(e.target, index)}
          onKeyDown={(e) => handleKeyDown(e, index)}
          onFocus={(e) => e.target.select()}
        />
      ))}
    </div>
  );
}