import React, { createContext, useReducer, useContext, ReactNode, Dispatch } from 'react';
import { ChatModel, Message, UserInfo } from './api/model';

// Define the shape of the state
interface State {
  isHistoryOpen: boolean;
  isRightPanelOpen: boolean;
  isDashBoardOpen: boolean;
  dashboardActiveTab: 'UserSettings' | 'UserActivityDashboard';
  rightPanel: 'profile' | 'knowledge_base' | 'notifications'| 'settings' | 'dashboard' | 
  'class_management';
  settings: 'chat_settings' | 'account_settings' | 'terms_conditions' | 'default' | 'user_lockout' | 'review_usage' | 'edit_class' | 'new_class';
  themeMode: 'light' | 'dark';
  isNewChat: boolean;
  chat?: ChatModel;
  chatName?: string;
  history: Message[];
  user: UserInfo;
  model: string;
  scrollPosition: number;
}

// Define the shape of actions
interface Action {
  type: 'TOGGLE_HISTORY' | 'TOGGLE_RIGHT_PANEL' | 'TOGGLE_PROFILE' | 'OPEN_PROFILE' | 'OPEN_KB' | 'PROFILE_SETTINGS' | 'TOGGLE_THEME_MODE' | 'SET_CHAT_NAME' | 'NEW_CHAT' | 'LOAD_CHAT' | 'SET_HISTORY' | 'TOGGLE_DASHBOARD' | 'TOGGLE_USER_SETTINGS' | 'DASHBOARD_SETTINGS' | 'OPEN_USER_SETTINGS' | 'CLASS_MANAGEMENT_SETTINGS' | 'OPEN_CLASS_SETTING' | 'TOGGLE_CLASS_SETTING' | 'DASHBOARD_TAB' | 'SET_USER' | 'SET_MODEL' | 'RENAME_CHAT';
  payload: any;
}

// Initial state
const initialState: State = {
  isHistoryOpen: false,
  isRightPanelOpen: false,
  isDashBoardOpen: false,
  dashboardActiveTab: 'UserActivityDashboard',
  rightPanel: 'profile',
  settings: 'default',
  themeMode: localStorage.getItem("theme-mode") === "light" ? 'light' : 'dark',
  isNewChat: true,
  chatName: '',
  history: [],
  user: {
    createdAt: '',
    email: '',
    id: '',
    updatedAt: '',
    firstName: '',
    lastName: ''
  },
  model: 'gemini-1.5-pro',
  scrollPosition: 0
};

// Create context with initial state type
const StateContext = createContext<{
  state: State;
  dispatch: Dispatch<Action>;
}>({
  state: initialState,
  dispatch: () => null
});

// Reducer function
const reducer = (state: State, action: Action): State => {
  switch (action.type) {
    case 'TOGGLE_HISTORY':
      return {
        ...state,
        isHistoryOpen: !state.isHistoryOpen
      };
    case 'TOGGLE_RIGHT_PANEL':
      return {
        ...state,
        isRightPanelOpen: !state.isRightPanelOpen,
        rightPanel: 'profile'
      };
    case 'TOGGLE_PROFILE':
      return {
        ...state,
        isRightPanelOpen: !state.isRightPanelOpen,
        rightPanel: 'profile'
      };
    case 'OPEN_PROFILE':
      return {
        ...state,
        rightPanel: 'profile'
      };
    case 'OPEN_KB':
      return {
        ...state,
        isRightPanelOpen: true,
        rightPanel: 'knowledge_base'
      };
    case 'PROFILE_SETTINGS':
      return {
        ...state,
        isRightPanelOpen: true,
        settings: action.payload.setting,
        rightPanel: 'settings'
      };
    case 'TOGGLE_THEME_MODE':
      return {
        ...state,
        themeMode: state.themeMode === 'light' ? 'dark' : 'light'
      };
    case 'SET_CHAT_NAME':
      return {
        ...state,
        isNewChat: false,
        chat: action.payload,
        chatName: action.payload.name
      };
    case 'TOGGLE_DASHBOARD':
      return {
        ...state,
        isDashBoardOpen: action.payload.isDashBoardOpen,
      };
    case 'TOGGLE_USER_SETTINGS':
      return {
        ...state,
        isRightPanelOpen: !state.isRightPanelOpen,
        rightPanel: 'dashboard'
      };
    case 'OPEN_USER_SETTINGS':
      return {
        ...state,
        rightPanel: 'dashboard'
      };
    case 'DASHBOARD_SETTINGS':
      return {
        ...state,
        isRightPanelOpen: true,
        settings: action.payload.setting,
        rightPanel: 'settings'
      };
    case 'CLASS_MANAGEMENT_SETTINGS':
      return {
        ...state,
        isRightPanelOpen: action.payload.isRightPanelOpen,
        rightPanel: 'class_management'
      };
    case 'TOGGLE_CLASS_SETTING':
      return {
        ...state,
        settings: action.payload.setting,
        rightPanel: 'settings'
      };
    case 'OPEN_CLASS_SETTING':
      return {
        ...state,
        rightPanel: 'class_management'
      };
    case 'NEW_CHAT':
      return {
        ...state,
        isNewChat: true,
        chat: undefined
      };
    case 'LOAD_CHAT':
      return {
        ...state,
        isNewChat: false,
        chat: undefined
      };
    case 'SET_HISTORY':
      return {
        ...state,
        history: action.payload,
        scrollPosition: state.scrollPosition + 1
      };
    case 'DASHBOARD_TAB':
      return {
        ...state,
        dashboardActiveTab: action.payload.tab
      };
    case 'SET_USER':
      return {
        ...state,
        user: action.payload
      };
    case 'SET_MODEL':
      return {
        ...state,
        model: action.payload
      };
    case 'RENAME_CHAT':
      return {
        ...state,
        chatName: action.payload
      };
    default:
      return state;
  }
};

// StateProvider component
export const StateProvider = ({ children }: { children: ReactNode }) => {
  const [state, dispatch] = useReducer(reducer, initialState);

  return (
    <StateContext.Provider value={{ state, dispatch }}>
      {children}
    </StateContext.Provider>
  );
};

// Custom hook to use the state context
export const useStateContext = () => useContext(StateContext);