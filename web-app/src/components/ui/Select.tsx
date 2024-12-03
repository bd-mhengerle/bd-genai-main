import React, { useState, useEffect, useRef } from 'react';
import styled from 'styled-components';
import { Reg_11, Reg_14 } from '../styling/typography';
import { ReactComponent as ChevronDown } from '../../assets/icons/chevron-down.svg';

interface SelectProps {
  value: string;
  label: string;
  width?: string;
  items: {id: string, text: string}[];
  onChange?: (value: any) => void
}

const Wrapper = styled.div<{ width?: string }>`
display: flex;
position: relative;
padding: 10px 0;
width: ${(props) => props.width}
`

const SelectContainer = styled.div<{ width?: string }>`
    border: 0.5px solid var(--pill-border);
    border-radius: 8px;
    height: 40px;
    display: grid;
    grid-template-columns: auto 30px;
    padding: 2.5px 15px;
    width: ${(props) => props.width}
`

const Field = styled.div`
    display: grid;
    grid-template-rows: 40% 60%;
    align-items: center;
`
const Icon = styled.div`
    display: flex;
    align-items: center;
    justify-content: end;
    cursor: pointer;
`
const DropdownList = styled.div`
    display: block;
    position: absolute;
    background-color: var(--background);
    min-width: 160px;
    box-shadow: 0px 8px 16px 0px rgba(0, 0, 0, 0.5);
    z-index: 1;
    width: 100%;
    top: 40px;

    & a {
        color: var(--font-color);
        padding: 12px 16px;
        text-decoration: none;
        display: block;
    }
    & a:hover {
        background-color: var(--background-hover);
    }
`

export const Select: React.FC<SelectProps> = ({ value, label, width, items, onChange }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [componentValue, setcomponentValue] = useState(items.find(x => x.id === value));
  const dropdownRef = useRef<HTMLDivElement>(null);

  const toggleDropdown = () => setIsOpen(!isOpen);

  const handleClickOutside = (event: MouseEvent) => {
    if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
      setIsOpen(false);
    }
  };

  useEffect(() => {
    document.addEventListener('click', handleClickOutside, true);
    return () => {
      document.removeEventListener('click', handleClickOutside, true);
    };
  }, []);

  return (
    <Wrapper width={width}>
    <SelectContainer width={width}>
        <Field>
            <Reg_11 style={{"color": "var(--regular-label-color)"}}>{label}</Reg_11>
            <Reg_14>{componentValue?.text}</Reg_14>
        </Field>
        <Icon onClick={() => setIsOpen(!isOpen)}>
            <ChevronDown style={{transform: isOpen ? 'rotate(180deg)': ''}}/>
        </Icon>
        <input type="hidden"/>
    </SelectContainer>
    {isOpen && (
        <DropdownList onClick={(e) => e.stopPropagation()}>
            {items.map(x => {
                return <a style={{"cursor": "pointer"}} onClick={() => {
                    setcomponentValue(items.find(i => i.id === x.id))
                    onChange && onChange(x.id)
                    toggleDropdown()
                }}>
                    <Reg_14>{x.text}</Reg_14>
                </a>
            })}
          {/* <a href="#rename" >Rename</a>
          <a href="#favourite" onClick={() => alert("Favourite")}>Favorite</a>
          <a href="#share" >Share</a>
          <a href="#delete" onClick={() => alert("Delete")}>Delete</a> */}
        </DropdownList>
      )}
    </Wrapper>
  );
};