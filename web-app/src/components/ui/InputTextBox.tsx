import React, { useState, useEffect, useRef } from 'react';
import styled from 'styled-components';
import { Reg_11, Reg_14 } from '../styling/typography';
import { ReactComponent as ChevronDown } from '../../assets/icons/chevron-down.svg';

interface InputProps {
  value: string;
  label: string;
  width?: string;
  onChange?: (value: any) => void
}

const Wrapper = styled.div<{ width?: string }>`
display: flex;
position: relative;
width: ${(props) => props.width}
`

const SelectContainer = styled.div<{ width?: string }>`
    border: 0.5px solid var(--pill-border);
    border-radius: 8px;
    height: 40px;
    display: flex;
    padding: 2.5px 15px;
    width: ${(props) => props.width}
`

const Field = styled.div`
    display: grid;
    grid-template-rows: 40% 60%;
    align-items: center;
    width: 100%;
`
const TextBox = styled.input`
    type: text;
    display: flex;
    align-items: center;
    font-family: Montserrat;
    font-size: 14px;
    font-weight: 500;
    line-height: 17.07px;
    letter-spacing: -0.02em;
    text-align: left;
    padding: 0;
    border: none;
    background-color: var(--background);
    color: var(--font-color);
    &:focus {
      outline: none;
      border: none;
    }
`

export const InputTextBox: React.FC<InputProps> = ({ value, label, width, onChange }) => {


  return (
    <Wrapper width={width}>
    <SelectContainer width={width}>
        <Field>
            <Reg_11 style={{"color": "var(--regular-label-color)"}}>{label}</Reg_11>
            <TextBox value={value} onChange={(e)=>{onChange && onChange(e.target.value)}}></TextBox>
        </Field>
    </SelectContainer>
    </Wrapper>
  );
};