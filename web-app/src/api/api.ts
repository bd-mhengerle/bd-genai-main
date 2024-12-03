import { ApiResponse } from "../models/ApiResponse";
import { ChatModel, CreateKbResponse, FileModel, FilesKbResponse, KnowledgeBaseModel, Message, SignedFile, UserInfo, UserActivityInfo } from "./model";


const createHeader = (headers: { [k: string]: string }) : Headers => {
    let header = new Headers()
    if(process.env.REACT_APP_API_TOKEN) {
        header.append('Authorization', 'Bearer '+process.env.REACT_APP_API_TOKEN)
    }
    for (const [key, value] of Object.entries(headers)) {
        header.append(key, value)
    }
    return header;
}

export const uploadFiles = async (kbId: string, files: File[]) : Promise<ApiResponse<string>> => {
    let response: ApiResponse<string> = {
        data: '',
        message: '',
        statusCode: 400,
        success: false
    };
    const formData = new FormData();
    files.forEach((file) => {
      formData.append("files", file);
    });
    const header = createHeader({})
    const result = await fetch(`${process.env.REACT_APP_API_BASE_URL}/upload`, {
        method: "POST",
        body: formData,
        headers: header
    });
    if (!result.ok) {
        response.data = "Network response was not ok"
        response.success = false
        response.statusCode = result.status
    } else {
        const responseData = await result.json();
        if (responseData.files && responseData.files.id) {
            response.data = "File(s) uploaded successfully!"
            response.success = true
            response.statusCode = 200
        } else {
            response.data = "Failed to upload files."
            response.success = false
            response.statusCode = result.status
        }
    }
    
    return response;
}

export const fetchChat = async (id: string) : Promise<ApiResponse<ChatModel|undefined>> => {
    let response: ApiResponse<ChatModel|undefined> = {
        data: undefined,
        message: '',
        statusCode: 400,
        success: false
    };
    const header = createHeader({})
    const result = await fetch(`${process.env.REACT_APP_API_BASE_URL}/chat/${id}`, {
      method: "GET",
      headers: header
    });
    if (!result.ok) {
        response.message = "Network response was not ok"
        response.success = false
        response.statusCode = result.status
    } else {
        const responseData = await result.json();
        if (responseData) {
            response.data = responseData
            response.success = true
            response.statusCode = 200
        } else {
            response.message = "No data loaded"
            response.success = false
            response.statusCode = result.status
        }
    }
    return response
}

const getChatsData = async (filters: string, limit: number): Promise<ApiResponse<ChatModel[]>> => {
    let response: ApiResponse<ChatModel[]> = {
        data: [],
        message: '',
        statusCode: 400,
        success: false
    };
    const header = createHeader({})
    const result = await fetch(`${process.env.REACT_APP_API_BASE_URL}/chat/listing?limit=${limit}&${filters}`, {
        headers: header
    });

    if (!result.ok) {
        response.success = false
        response.statusCode = result.status
    } else {
        const responseData = await result.json();
        response.data = responseData.data
        response.statusCode = 200
        response.success = true
    }
    return response
};

export const getFavorites = async(): Promise<ApiResponse<ChatModel[]>> => {
    const response = await getChatsData("filters=favorite:==:true", 5)
    return response
}

export const getTodays = async (): Promise<ApiResponse<ChatModel[]>> => {
    const today = new Date();
    const yesterday = new Date(today)
    yesterday.setDate(today.getDate() - 1)
    const response = await getChatsData(`filters=favorite:==:false&filters=createdAt:>=:${yesterday.toISOString()}&filters=createdAt:<:${today.toISOString()}`, 5)
    return response
}

export const getSevenDaysAgo = async (): Promise<ApiResponse<ChatModel[]>> => {
    const today = new Date();
    const yesterday = new Date(today)
    yesterday.setDate(today.getDate() - 1)
    const sevenDaysAgo = new Date(today)
    sevenDaysAgo.setDate(today.getDate() - 7)
    const response = await getChatsData(`filters=favorite:==:false&filters=createdAt:>=:${sevenDaysAgo.toISOString()}&filters=createdAt:<:${yesterday.toISOString()}`, 10)
    return response
}

export const getThirtyDaysAgo = async (): Promise<ApiResponse<ChatModel[]>> => {
    const today = new Date();
    const sevenDaysAgo = new Date(today)
    sevenDaysAgo.setDate(today.getDate() - 7)
    const thirtyDaysAgo = new Date(today)
    thirtyDaysAgo.setDate(today.getDate() - 30)
    const response = await getChatsData(`filters=favorite:==:false&filters=createdAt:>=:${thirtyDaysAgo.toISOString()}&filters=createdAt:<:${sevenDaysAgo.toISOString()}`, 30)
    return response
}
//

export const markAsFavorite = async (id: string): Promise<ApiResponse<boolean | undefined>> => {
    let response: ApiResponse<boolean | undefined> = {
        data: undefined,
        message: '',
        statusCode: 400,
        success: false
    };
    const header = createHeader({"Content-Type": "application/json"})
    const result = await fetch(`${process.env.REACT_APP_API_BASE_URL}/chat/${id}/favorite`, {
        method: "POST",
        headers: header
    });

    if (!result.ok) {
        response.message = "Request couldn't be completed"
        response.success = false
        response.statusCode = result.status
    } else {
        const responseData = await result.json();
        response.data = responseData.favorite
        response.message = "Chat marked as favorite"
        response.statusCode = 200
        response.success = true
    }
    return response
}

export const createChat = async (name: string): Promise<ApiResponse<string>> => {
    let response: ApiResponse<string> = {
        data: '',
        message: '',
        statusCode: 400,
        success: false
    };
    const header = createHeader({"Content-Type": "application/json"})
    const result = await fetch(`${process.env.REACT_APP_API_BASE_URL}/chat`, {
        method: "POST",
        headers: header,
        body: JSON.stringify({ name: name, tags: [], id: '' }),
    });

    if (!result.ok) {
        response.message = "Chat couldn't be created"
        response.success = false
        response.statusCode = result.status
    } else {
        const responseData = await result.json();
        const chatId = responseData.data && responseData.data.id
        response.data = chatId
        response.message = 'Chat created successfully'
        response.statusCode = 200
        response.success = true
    }
    return response
}

export const updateChat = async (id: string, name: string, tags: string[]): Promise<ApiResponse<void>> => {
    let response: ApiResponse<void> = {
        data: undefined,
        message: '',
        statusCode: 400,
        success: false
    };
    const header = createHeader({"Content-Type": "application/json"})
    const result = await fetch(`${process.env.REACT_APP_API_BASE_URL}/chat/${id}`, {
        method: "PUT",
        headers: header,
        body: JSON.stringify({ name: name, tags: tags }),
    });

    if (!result.ok) {
        response.message = "Chat couldn't be updated"
        response.success = false
        response.statusCode = result.status
    } else {
        response.message = 'Chat updated successfully'
        response.statusCode = 200
        response.success = true
    }
    return response
}

export const deleteChat = async (id: string): Promise<ApiResponse<void>> => {
    let response: ApiResponse<void> = {
        data: undefined,
        message: '',
        statusCode: 400,
        success: false
    };
    const header = createHeader({"Content-Type": "application/json"})
    const result = await fetch(`${process.env.REACT_APP_API_BASE_URL}/chat/${id}`, {
        method: "DELETE",
        headers: header
    });

    if (!result.ok) {
        response.message = "Chat couldn't be deleted"
        response.success = false
        response.statusCode = result.status
    } else {
        response.message = 'Chat deleted successfully'
        response.statusCode = 200
        response.success = true
    }
    return response
}

export const askToBot = async (chatId: string, message: string, kbs: string[], model: string): Promise<ApiResponse<Message | undefined>>  => {
    let response: ApiResponse<Message | undefined> = {
        data: undefined,
        message: '',
        statusCode: 400,
        success: false
    };
    const header = createHeader({"Content-Type": "application/json"})
    console.log(`${process.env.REACT_APP_API_BASE_URL}/chat/${chatId}/ask`)
    const result = await fetch(`${process.env.REACT_APP_API_BASE_URL}/chat/${chatId}/ask`, {
        method: "POST",
        headers: header,
        body: JSON.stringify({ question: message, knowledge_base_ids: kbs, model: model }),
    });
  
    if (!result.ok) {
        response.message = "Something went wrong"
        response.success = false
        response.statusCode = result.status
    } else {
        const responseData = await result.json();
        response.data = responseData.data
        response.message = ''
        response.statusCode = 200
        response.success = true
    }
    return response
  }

  export const getPublicKbs = async (): Promise<ApiResponse<KnowledgeBaseModel[]>> => {
    let response: ApiResponse<KnowledgeBaseModel[]> = {
        data: [],
        message: '',
        statusCode: 400,
        success: false
    };
    const header = createHeader({})
    const result = await fetch(`${process.env.REACT_APP_API_BASE_URL}/kb/listing/user/public`, {
        headers: header
    });

    if (!result.ok) {
        response.success = false
        response.statusCode = result.status
    } else {
        const responseData = await result.json();
        response.data = responseData.data
        response.statusCode = 200
        response.success = true
    }
    return response
};

export const getPrivateKbs = async (): Promise<ApiResponse<KnowledgeBaseModel[]>> => {
    let response: ApiResponse<KnowledgeBaseModel[]> = {
        data: [],
        message: '',
        statusCode: 400,
        success: false
    };
    const header = createHeader({})
    const result = await fetch(`${process.env.REACT_APP_API_BASE_URL}/kb/listing/user/private`, {
        headers: header
    });

    if (!result.ok) {
        response.success = false
        response.statusCode = result.status
    } else {
        const responseData = await result.json();
        response.data = responseData.data
        response.statusCode = 200
        response.success = true
    }
    return response
};

export const getPredefinedKbs = async (): Promise<ApiResponse<KnowledgeBaseModel[]>> => {
    let response: ApiResponse<KnowledgeBaseModel[]> = {
        data: [],
        message: '',
        statusCode: 400,
        success: false
    };
    const header = createHeader({})
    const result = await fetch(`${process.env.REACT_APP_API_BASE_URL}/kb/listing/predefined`, {
        headers: header
    });

    if (!result.ok) {
        response.success = false
        response.statusCode = result.status
    } else {
        const responseData = await result.json();
        response.data = responseData.data
        response.statusCode = 200
        response.success = true
    }
    return response
};

export const getFileById = async (id: string): Promise<ApiResponse<FileModel | undefined>> => {
    let response: ApiResponse<FileModel | undefined> = {
        data: undefined,
        message: '',
        statusCode: 400,
        success: false
    };
    const header = createHeader({})
    const result = await fetch(`${process.env.REACT_APP_API_BASE_URL}/files/listing?filters=id:==:${id}`, {
        headers: header
    });

    if (!result.ok) {
        response.success = false
        response.statusCode = result.status
    } else {
        const responseData = await result.json();
        response.data = responseData.data.length ? responseData.data[0] : null
        response.statusCode = 200
        response.success = true
    }
    return response
};

export const getUserInfo = async (): Promise<ApiResponse<UserInfo | undefined>> => {
    let response: ApiResponse<UserInfo | undefined> = {
        data: undefined,
        message: '',
        statusCode: 400,
        success: false
    };
    const header = createHeader({
        "Authorization": "Bearer "+process.env.REACT_APP_API_TOKEN
    })
    const result = await fetch(`${process.env.REACT_APP_API_BASE_URL}/user/me`, {
        headers: header
    });
    if (!result.ok) {
        response.success = false
        response.statusCode = result.status
    } else {
        const responseData = await result.json();
        response.data = responseData.data;
        response.statusCode = 200
        response.success = true
    }
    return response
};

export const getUserActivity = async (filters: string): Promise<ApiResponse<UserActivityInfo[] | undefined>> => {
    let response: ApiResponse<UserActivityInfo[] | undefined> = {
        data: undefined,
        message: '',
        statusCode: 400,
        success: false
    };
    const header = createHeader({
        "Authorization": "Bearer "+process.env.REACT_APP_API_TOKEN
    })
    const result = await fetch(`${process.env.REACT_APP_API_BASE_URL}/report/user-activity?${filters}`, {
        headers: header
    });
    if (!result.ok) {
        response.success = false
        response.statusCode = result.status
    } else {
        const responseData = await result.json();
        response.data = responseData.data;
        response.statusCode = 200
        response.success = true
    }
    return response
};

export const getNewChats = async (): Promise<ApiResponse<number>> => {
    let response: ApiResponse<number> = {
        data: 0,
        message: '',
        statusCode: 400,
        success: false
    };
    const header = createHeader({
        "Authorization": "Bearer "+process.env.REACT_APP_API_TOKEN
    })
    const result = await fetch(`${process.env.REACT_APP_API_BASE_URL}/report/aggregation/count/new-chats`, {
        headers: header
    });
    if (!result.ok) {
        response.success = false
        response.statusCode = result.status
    } else {
        const responseData = await result.json();
        console.log("new chats: ", responseData.total)
        response.data = responseData.total;
        response.statusCode = 200
        response.success = true
    }
    return response
};

export const getNewMsgs = async (): Promise<ApiResponse<number>> => {
    let response: ApiResponse<number> = {
        data: 0,
        message: '',
        statusCode: 400,
        success: false
    };
    const header = createHeader({
        "Authorization": "Bearer "+process.env.REACT_APP_API_TOKEN
    })
    const result = await fetch(`${process.env.REACT_APP_API_BASE_URL}/report/aggregation/count/msgs`, {
        headers: header
    });
    if (!result.ok) {
        response.success = false
        response.statusCode = result.status
    } else {
        const responseData = await result.json();
        response.data = responseData.total;
        response.statusCode = 200
        response.success = true
    }
    return response
};

export const getNewUploads = async (): Promise<ApiResponse<number>> => {
    let response: ApiResponse<number> = {
        data: 0,
        message: '',
        statusCode: 400,
        success: false
    };
    const header = createHeader({
        "Authorization": "Bearer "+process.env.REACT_APP_API_TOKEN
    })
    const result = await fetch(`${process.env.REACT_APP_API_BASE_URL}/report/aggregation/count/uploads`, {
        headers: header
    });
    if (!result.ok) {
        response.success = false
        response.statusCode = result.status
    } else {
        const responseData = await result.json();
        response.data = responseData.total;
        response.statusCode = 200
        response.success = true
    }
    return response
};

export const getNewKbs = async (): Promise<ApiResponse<number>> => {
    let response: ApiResponse<number> = {
        data: 0,
        message: '',
        statusCode: 400,
        success: false
    };
    const header = createHeader({
        "Authorization": "Bearer "+process.env.REACT_APP_API_TOKEN
    })
    const result = await fetch(`${process.env.REACT_APP_API_BASE_URL}/report/aggregation/count/new-kbs`, {
        headers: header
    });
    if (!result.ok) {
        response.success = false
        response.statusCode = result.status
    } else {
        const responseData = await result.json();
        response.data = responseData.total;
        response.statusCode = 200
        response.success = true
    }
    return response
};

export const getResumedChats = async (): Promise<ApiResponse<number>> => {
    let response: ApiResponse<number> = {
        data: 0,
        message: '',
        statusCode: 400,
        success: false
    };
    const header = createHeader({
        "Authorization": "Bearer "+process.env.REACT_APP_API_TOKEN
    })
    const result = await fetch(`${process.env.REACT_APP_API_BASE_URL}/report/aggregation/count/resumed-chats`, {
        headers: header
    });
    if (!result.ok) {
        response.success = false
        response.statusCode = result.status
    } else {
        const responseData = await result.json();
        response.data = responseData.total;
        response.statusCode = 200
        response.success = true
    }
    return response
};

export const createKb = async (name: string, isPublic: boolean): Promise<ApiResponse<CreateKbResponse | undefined>> => {
    let response: ApiResponse<CreateKbResponse | undefined> = {
        data: undefined,
        message: '',
        statusCode: 400,
        success: false
    };
    const header = createHeader({"Content-Type": "application/json"})
    const result = await fetch(`${process.env.REACT_APP_API_BASE_URL}/kb`, {
        method: "POST",
        headers: header,
        body: JSON.stringify({ name: name, public: isPublic }),
    });

    if (!result.ok) {
        response.message = "Knowledge base couldn't be created"
        response.success = false
        response.statusCode = result.status
    } else {
        const responseData = await result.json();
        response.data = responseData
        response.message = 'Knowledge base created successfully'
        response.statusCode = 200
        response.success = true
    }
    return response
}

export const updateKb = async (id: string, name: string, isPublic: boolean): Promise<ApiResponse<CreateKbResponse | undefined>> => {
    let response: ApiResponse<CreateKbResponse | undefined> = {
        data: undefined,
        message: '',
        statusCode: 400,
        success: false
    };
    const header = createHeader({"Content-Type": "application/json"})
    const result = await fetch(`${process.env.REACT_APP_API_BASE_URL}/kb/${id}`, {
        method: "PUT",
        headers: header,
        body: JSON.stringify({ name: name, public: isPublic }),
    });

    if (!result.ok) {
        response.message = "Knowledge base couldn't be updated"
        response.success = false
        response.statusCode = result.status
    } else {
        const responseData = await result.json();
        response.data = responseData
        response.message = 'Knowledge base updated successfully'
        response.statusCode = 200
        response.success = true
    }
    return response
}

export const addFilesToKb = async (id: string, files: File[]): Promise<ApiResponse<FilesKbResponse | undefined>> => {
    let response: ApiResponse<FilesKbResponse | undefined> = {
        data: undefined,
        message: '',
        statusCode: 400,
        success: false
    };
    const formData = new FormData();
    files.forEach((file) => {
      formData.append("files", file);
    });
    const header = createHeader({})
    const result = await fetch(`${process.env.REACT_APP_API_BASE_URL}/kb/${id}/add/files`, {
        method: "POST",
        headers: header,
        body: formData
    });

    if (!result.ok) {
        response.message = "Knowledge base couldn't be created"
        response.success = false
        response.statusCode = result.status
    } else {
        const responseData = await result.json();
        response.data = responseData
        response.message = 'Knowledge base created successfully'
        response.statusCode = 200
        response.success = true
    }
    return response
}

export const deleteFilesFromKb = async (id: string, files: string[]): Promise<ApiResponse<FilesKbResponse | undefined>> => {
    let response: ApiResponse<FilesKbResponse | undefined> = {
        data: undefined,
        message: '',
        statusCode: 400,
        success: false
    };
    const header = createHeader({"Content-Type": "application/json"})
    const result = await fetch(`${process.env.REACT_APP_API_BASE_URL}/kb/${id}/remove/files`, {
        method: "POST",
        headers: header,
        body: JSON.stringify({ file_ids: files }),
    });

    if (!result.ok) {
        response.message = "File couldn't be removed"
        response.success = false
        response.statusCode = result.status
    } else {
        const responseData = await result.json();
        response.data = responseData
        response.message = 'File removed successfully'
        response.statusCode = 200
        response.success = true
    }
    return response
}

export const deleteKb = async (id: string): Promise<ApiResponse<void>> => {
    let response: ApiResponse<void> = {
        data: undefined,
        message: '',
        statusCode: 400,
        success: false
    };
    const header = createHeader({"Content-Type": "application/json"})
    const result = await fetch(`${process.env.REACT_APP_API_BASE_URL}/kb/${id}`, {
        method: "DELETE",
        headers: header,
    });

    if (!result.ok) {
        response.message = "Knowledge base couldn't be removed"
        response.success = false
        response.statusCode = result.status
    } else {
        response.message = 'Knowledge base removed successfully'
        response.statusCode = 200
        response.success = true
    }
    return response
} 

export const getSignedFile = async (file: string): Promise<ApiResponse<SignedFile | undefined>> => {
    let response: ApiResponse<SignedFile | undefined> = {
        data: undefined,
        message: '',
        statusCode: 400,
        success: false
    };
    const header = createHeader({})
    const result = await fetch(`${process.env.REACT_APP_API_BASE_URL}/files/signed?blob_name=${file}`, {
        headers: header
    });
    if (!result.ok) {
        response.success = false
        response.statusCode = result.status
    } else {
        const responseData = await result.json();
        response.data = responseData.data;
        response.statusCode = 200
        response.success = true
    }
    return response
};