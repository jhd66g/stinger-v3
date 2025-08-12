import React, { useState, useRef, useEffect } from 'react'

const RangeSlider = ({ min, max, value, onChange, formatValue = (val) => val }) => {
  const [dragTarget, setDragTarget] = useState(null)
  const sliderRef = useRef(null)

  const [minVal, maxVal] = value

  const getPercent = (val) => ((val - min) / (max - min)) * 100

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!dragTarget || !sliderRef.current) return

      const rect = sliderRef.current.getBoundingClientRect()
      const percent = Math.max(0, Math.min(100, ((e.clientX - rect.left) / rect.width) * 100))
      const newValue = Math.round((percent / 100) * (max - min) + min)

      if (dragTarget === 'min') {
        const newMinVal = Math.min(newValue, maxVal - 1)
        onChange([newMinVal, maxVal])
      } else {
        const newMaxVal = Math.max(newValue, minVal + 1)
        onChange([minVal, newMaxVal])
      }
    }

    const handleMouseUp = () => {
      setDragTarget(null)
    }

    if (dragTarget) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [dragTarget, max, min, maxVal, minVal, onChange])

  const handleMouseDown = (e, target) => {
    setDragTarget(target)
  }

  return (
    <div className="range-slider">
      <div
        ref={sliderRef}
        className="range-slider__track"
        style={{ position: 'relative' }}
      >
        <div
          className="range-slider__fill"
          style={{
            left: `${getPercent(minVal)}%`,
            width: `${getPercent(maxVal) - getPercent(minVal)}%`
          }}
        />
        <div
          className="range-slider__thumb"
          style={{ left: `${getPercent(minVal)}%` }}
          onMouseDown={(e) => handleMouseDown(e, 'min')}
        />
        <div
          className="range-slider__thumb"
          style={{ left: `${getPercent(maxVal)}%` }}
          onMouseDown={(e) => handleMouseDown(e, 'max')}
        />
      </div>
      <div className="range-slider__values">
        <span>{formatValue(minVal)}</span>
        <span>{formatValue(maxVal)}</span>
      </div>
    </div>
  )
}

export default RangeSlider
