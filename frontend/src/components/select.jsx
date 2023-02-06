import { useState, useMemo, useEffect } from 'react'
import Dialog from './dialog'
import { InputText } from './input'
import { Button } from './button'
import { sortByKey } from '/src/utils'
import styled from 'styled-components'
import defaultTheme from './theme'


const ButtonWrapper = styled.div`
  display: flex;
  flex-direction: row;
  gap: 6px;
  justify-content: flex-start;
  border-top: 1px solid ${(props) => props.theme.colors.surface04};
  padding-top: 10px;

  button {
    min-width: 100px;
  }
`
ButtonWrapper.defaultProps = {
  theme: defaultTheme,
}


const BaseOption = styled.div`
  padding: 3px;
  cursor: pointer;
  white-space: nowrap;
  background-color: ${(props) => props.theme.colors.surface05};

  &.selected{
    background-color: ${(props) => props.theme.colors.violet};
  }

  &.label{
    font-weight: bold;
    background-color: ${(props) => props.theme.colors.surface03};
  }

  &.header{
    font-weight: bold;
  }
`
BaseOption.defaultProps = {
  theme: defaultTheme,
}


const Option = ({ option, selected, onClick }) => {
  const classes = []
  if (selected) classes.push('selected')
  if (option.role === "label") classes.push('label')
  return (
    <BaseOption
      className={classes.join(' ')}
      style={{ paddingLeft: option.level * 15 }}
      onClick={option.role === "label" ? undefined : onClick}
      title={option.description}
    >
      {option.title}
    </BaseOption>
  )
}


function filterHierarchy(array, query, currentSelection) {
  const queryLower = query.toLowerCase();
  const result = [];
  const set = new Set();
  for (const item of array) {
    item.level = item.value.split('.').length
    if (item.title.toLowerCase().includes(queryLower) || item.value in currentSelection) {
      if (item.role === "hidden") {
        continue
      }
      result.push(item);
      set.add(item.value);
      let value = item.value;
      while (value) {
        const parts = value.split(".");
        if (parts.length === 1) {
          value = "";
        } else {
          parts.pop();
          value = parts.join(".");
          const parent = array.find((i) => i.value === value);
          if (item.role !== "hidden" && parent && !set.has(parent.value)) {
            result.push(parent);
            set.add(parent.value);
          }
        }
      }
    }
  }
  return sortByKey(result, "value");
}


const SelectDialog = ({ options, onHide, selectionMode, initialValue }) => {
  const [filter, setFilter] = useState('')
  const [selection, setSelection] = useState({})

  // Create the selection object from the given initial Value.

  useEffect(() => {
    if (selectionMode === 'single') {
      setSelection({ [initialValue]: true })
      return
    }
    const result = {}
    for (const r of initialValue || []) result[r] = true
    setSelection(result)
  }, [initialValue])

  const filteredOptions = useMemo(() => {
    return filterHierarchy(options, filter, selection)
  }, [options, filter, selection])

  const onToggle = (key) => {
    setSelection((os) => {
      if (selectionMode === 'single') return { [key]: true }
      const result = { ...os }
      result[key] = !os[key]
      return result
    })
  }

  const onClose = () => {
    onHide(initialValue)
  }

  const onUnset = () => {
    onHide(null)
  }

  const onApply = () => {
    let value = Object.keys(selection).filter((key) => selection[key])
    if (selectionMode === 'single') value = value.length ? value[0] : null
    onHide(value)
  }

  return (
    <Dialog onHide={() => onClose()} style={{ minWidth: 400 }}>
      <InputText placeholder="Filter" value={filter} onChange={setFilter} />

      <div className="scroll-box">
        <div className="scroll-box-cont">
          {filteredOptions.map((option) => (
            <Option
              key={option.value}
              option={option}
              selected={selection[option.value]}
              onClick={() => onToggle(option.value)}
            />
          ))}
        </div>
      </div>
      <ButtonWrapper>
        <Button onClick={() => onClose()} label="Cancel" />
        <Button onClick={() => onUnset()} label="Unset" />
        <Button onClick={() => onApply()} label="Apply" />
      </ButtonWrapper>
    </Dialog>
  )
}

// Styled dialog-based select component.

const DialogBasedSelect = styled.div`
  // pseudo-input element
  display: flex;
  flex-direction: row;
  gap: 4px;
  min-width: 200px;

  .select-field {
    flex-grow: 1;

    border: 0;
    border-radius: 4px;
    background-color: ${(props) => props.theme.colors.surface04};
    color: ${(props) => props.theme.colors.text};
    min-height: ${(props) => props.theme.inputHeight};
    font-size: ${(props) => props.theme.fontSize};
    padding-left: 5px;
    padding-right: 5px;
    position: relative;
    display: flex;
    align-items: center;

    span {
      position: absolute;
      width: 95%;
      text-overflow: ellipsis;
      white-space: nowrap;
      overflow: hidden;
    }
  }

  // TODO: move to separate component

  .scroll-box {
    flex-grow: 1;
    position: relative;

    .scroll-box-cont {
      position: relative;
      max-height: 400px;
      overflow-y: scroll;
      overflow-x: auto;
      display: flex;
      flex-direction: column;
      gap: 3px;
    }
  }

`
DialogBasedSelect.defaultProps = {
  theme: defaultTheme,
}



// When there is just a few items in the list, we can use a dropdown.

const StyledHTMLSelect = styled.select`
  border: 0;
  border-radius: ${(props) => props.theme.inputBorderRadius};
  background: ${(props) => props.theme.inputBackground};
  color: ${(props) => props.theme.colors.text};
  min-height: ${(props) => props.theme.inputHeight};
  font-size: ${(props) => props.theme.fontSize};
  padding-left: ${(props) => props.theme.inputPadding};
  padding-right: ${(props) => props.theme.inputPadding};
  min-width: 200px;

  &:focus {
    outline: 1px solid ${(props) => props.theme.colors.cyan};
  }

  &:hover {
    color: ${(props) => props.theme.colors.text};
  }

  &:invalid,
  &.error {
    outline: 1px solid ${(props) => props.theme.colors.red} !important;
  }
`
StyledHTMLSelect.defaultProps = {
  theme: defaultTheme,
}


const Select = ({ options, value, onChange, selectionMode = 'single' }) => {
  const [dialogVisible, setDialogVisible] = useState(false)

  const displayValue = useMemo(() => {
    let result = []
    if (!value) return
    for (const opt of options) {
      if (selectionMode === 'single' && value === opt.value) {
        result.push(opt.title)
        break
      } else if (selectionMode === 'multiple' && value.includes(opt.value))
        result.push(opt.title)
    }
    return result.join(', ')
  }, [options, value])

  const onDialogClose = (value) => {
    onChange(value)
    setDialogVisible(false)
  }

  let dialog = useMemo(() => {
    if (!dialogVisible) return <></>
    return (
      <SelectDialog
        options={options}
        selectionMode={selectionMode}
        initialValue={value}
        onHide={onDialogClose}
      />
    )
  }, [dialogVisible])


  if (selectionMode === 'single' && options.length < 10) {
    return (
      <StyledHTMLSelect value={value} onChange={(e) => onChange(e.target.value)}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.title}
          </option>
        ))}
      </StyledHTMLSelect>

    )
  }


  return (
    <DialogBasedSelect>
      {dialog}
      <div className="select-field" onClick={() => setDialogVisible(true)}>
        <span>{displayValue}</span>
      </div>
      <Button label="..." onClick={() => setDialogVisible(true)} />
    </DialogBasedSelect>
  )
}

export default Select