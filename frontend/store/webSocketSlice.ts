import { createSlice } from '@reduxjs/toolkit';
import { IScatter3dData } from '../util/interfaces';

// Type definitions for the state contained by this slice
interface IWebSocketSlice {
    scatterData: IScatter3dData[] | null;
}

const initialState: IWebSocketSlice = {
    scatterData: null
}

const webSocketSlice = createSlice({
    name: 'data',
    initialState,
    reducers: {
        setScatter: (state, action) => {
            state.scatterData = action.payload as IScatter3dData[];
        }
    }
})

export const webSocketActions = webSocketSlice.actions;

export default webSocketSlice;