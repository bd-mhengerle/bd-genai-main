export interface ChatModel {
    id: string;
    name: string;
    createdAt: Date;
    updatedAt: Date;
    isDeleted: boolean;
    favorite: boolean;
    files: string[];
    tags: string[];
    kbId: string;
    createdById: {email: string, id: string};
    history: Message[];
}

export interface Message {
    content: string;
    role: string;
    createdAt?: string;
    id: string;
    kbIds?: string[];
    model?: string;
    tokenNumber?: number;
    userEvaluation?: string;
    citations?: Citation[];
}

export interface KnowledgeBaseModel {
    createdAt: string;
    createdBy: {email: string, id: string};
    filesIds: string[];
    id: string;
    isDeleted: boolean;
    name: string;
    public: boolean;
    referenceId: string;
    tools: string[];
    type: string;
    updatedAt: string;
    ///////
    active?: boolean;
}

export interface Citation {
    citation: string;
}

export interface FileModel {
    authenticatedURL: string;
    createdAt: string;
    createdBy: {email: string, id: string}
    gcsPath: string;
    id: string;
    isDeleted: boolean;
    mimeType: string;
    name: string;
    sizeBytes: number;
}

export interface UserInfo {
    createdAt: string;
    email: string;
    id: string;
    updatedAt: string;
    firstName?: string;
    lastName?: string;
}

export interface UserActivityInfo {
    name: string;
    email: string;
    id: string;
    createdAt: string;
    updatedAt: string;
    isDeleted: boolean;
    newChat: number;
    questionsAsked: number;
    chatsResumed: number;
    documentsUploaded: number;
    knowledgeBaseCreated: number;
    documentsUploadTotalSizeBytes: number;
    lastMessageAt: string;
    lastCreatedChatAt: string;
    lastResumedChatAt: string;
    lastDocumentUploadedAt: string;
    lastKnowledgeBaseCreatedAt: string;
    tokensUsed: {
        model1: number;
        model2: number;
        model3: number;
    }
}

export interface CreateKbResponse {
    message: string;
    data: KnowledgeBaseModel;
}

export interface SignedFile {
    authenticatedURL: string;
}

export interface FilesKbResponse {
    embedding_results: {[key:string]: string};
    data: KnowledgeBaseModel;
}