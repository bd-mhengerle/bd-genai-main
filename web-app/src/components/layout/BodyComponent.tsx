import { ReactNode } from "react";
import styled from 'styled-components';
import { useStateContext } from "../../StateContext";

const Wrapper = styled.div<{ isHistoryOpen?: boolean, isRightPanelOpen?: boolean }>`
  border: 1px solid var(--White---Fade, var(--body-border));
  box-shadow: inset 0px 0px 18px 0px var(--box-shadow);
  background-color: var(--background-chat);
  border-radius: 20px 20px 0 0;
  padding: 10px;
  margin: 10px 10px 0 10px;
  grid-column-start: ${(props) => (props.isHistoryOpen ? '2' : '1')};
  grid-column-end: ${(props) => (props.isRightPanelOpen ? '3' : '4')};
  grid-row: 2;
`;
const BodyComponent = ({
  children,
}: {
    children?: ReactNode
}) => {
    const { state } = useStateContext();
    return (
        <Wrapper isHistoryOpen={state.isHistoryOpen} isRightPanelOpen={state.isRightPanelOpen}>
            {children}
        </Wrapper>
    );
};

export default BodyComponent;
