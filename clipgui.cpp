// ffmpeg libraries
extern "C"
{
    #include "libavcodec/avcodec.h"
    #include <libavformat/avformat.h>
    #include <libswscale/swscale.h>
}

// wxWidgets "clipmerge" GUI
#include <wx/wxprec.h>
#include <wx/filedlg.h>
#include <wx/utils.h> 
#include <wx/wfstream.h>

#include <stdio.h>
#include <string.h>
#include <stdlib.h>

// For compilers that support precompilation, includes "wx/wx.h".
#ifndef WX_PRECOMP
    #include <wx/wx.h>
#endif


class ClipMerge : public wxApp{
public:
    virtual bool OnInit();
};

class ClipFrame : public wxFrame{
public:
    ClipFrame();
    DECLARE_EVENT_TABLE();
private:
    int DEBUG = 0;
    wxArrayString audiofilepaths;
    wxString videofile;
    void onselectdir(wxCommandEvent& event);
    void onselectmp4(wxCommandEvent& event);
    void onselectmp3audio(wxCommandEvent& event);
    void onmerge(wxCommandEvent& event);
};

enum{
    BUTTON_Video = wxID_HIGHEST + 1
};

enum {
    BUTTON_Audio = BUTTON_Video + 1
};

enum {
    BUTTON_Merge = BUTTON_Audio + 1
};


BEGIN_EVENT_TABLE (ClipFrame, wxFrame )
    EVT_BUTTON ( BUTTON_Video, ClipFrame::onselectmp4 )
    EVT_BUTTON ( BUTTON_Audio, ClipFrame::onselectmp3audio )
    EVT_BUTTON ( BUTTON_Merge, ClipFrame::onmerge )
END_EVENT_TABLE()



wxIMPLEMENT_APP(ClipMerge);

bool ClipMerge::OnInit(){
    ClipFrame *clipframe = new ClipFrame();
    clipframe->Show(true);
    return true;
}


ClipFrame::ClipFrame() : wxFrame(NULL, wxID_ANY, "Merge Clips"){
    wxButton *btnSelectVideo;
    wxButton *btnSelectAudioFiles;
    wxButton *btnmerge;
    this->DEBUG = 1;
    wxPanel* videopanel = new wxPanel(this, wxID_ANY);
    btnSelectVideo =  new wxButton(videopanel, BUTTON_Video, _T("Select Video"), wxPoint(10,20), wxSize(150,100), wxBU_EXACTFIT);
    //wxPanel* audiopanel = new wxPanel(this, wxID_ANY);
    btnSelectAudioFiles =  new wxButton(videopanel, BUTTON_Audio, _T("Select Audio Files"), wxPoint(10,180), wxSize(150,100), wxBU_EXACTFIT);
    btnmerge = new wxButton(videopanel, BUTTON_Merge, _T("Merge Streams"), wxPoint(10,300), wxSize(150,100), wxBU_EXACTFIT);
    CreateStatusBar();
    SetStatusText("Welcome to ClipMerge!");
    // ffmpeg register all
    av_register_all();
}


void ClipFrame::onselectdir(wxCommandEvent& event){
    Close(true);
}


void ClipFrame::onselectmp4(wxCommandEvent& event){
     wxFileDialog openFileDialogVideo(this, _("Select mp4 video"), "", "", "mp4/avi files (*.mp4;*.avi)|*.mp4;*.avi", wxFD_OPEN|wxFD_FILE_MUST_EXIST);
     if (openFileDialogVideo.ShowModal() == wxID_CANCEL)
        return;
     this->videofile = openFileDialogVideo.GetPath();
     if (!this->videofile|| this->videofile == ""){
        wxLogError("Cannot open file '%s'.", openFileDialogVideo.GetPath());
        return;
     }
}


void ClipFrame::onselectmp3audio(wxCommandEvent& event){
     wxFileDialog openFileDialogAudio(this, _("Select mp3 files"), "", "", "mp3 files (*.mp3)|*.mp3", wxFD_OPEN|wxFD_FILE_MUST_EXIST|wxFD_MULTIPLE);
     
     if (openFileDialogAudio.ShowModal() == wxID_CANCEL)
        return;
     openFileDialogAudio.GetPaths(this->audiofilepaths);
     if (this->audiofilepaths.GetCount() == 0){
        wxLogError("Could not get audio files.");
        return;
     }
}


void ClipFrame::onmerge(wxCommandEvent& event){
    if(this->DEBUG == 1){
        wxLogMessage(this->videofile);
        for(int i=0; i < this->audiofilepaths.GetCount(); i++){
            wxLogMessage(this->audiofilepaths[i]);
        }
    }
}

// ffmpeg functions
int64_t getvideoduration(wxString mp4path){
    char *strmp4path;
    int64_t duration;
    AVFormatContext *pFormatCtx = NULL;
    strmp4path = (char *)malloc(sizeof(mp4path));
    strcpy(strmp4path, mp4path.mb_str(wxConvUTF8));
    if(avformat_open_input(&pFormatCtx, strmp4path, NULL, 0) != 0)
        return -1; // Couldn't open file
    // Find the first video stream
    if(avformat_find_stream_info(pFormatCtx, NULL) < 0)
        return -1; // Couldn't find stream information
    duration = pFormatCtx->duration;
    // Done, got duration in seconds
    avformat_close_input(&pFormatCtx);
    avformat_free_context(pFormatCtx);
    return (duration);
}

int64_t getaudioduration(wxString mp3path){
    char *strmp3path;
    int64_t duration;
    AVPacket *pkt;
    int readbytes = 0;
    AVFormatContext *pFormatCtx = NULL;
    strmp3path = (char *)malloc(sizeof(mp3path));
    strcpy(strmp3path, mp3path.mb_str(wxConvUTF8));
    if(avformat_open_input(&pFormatCtx, strmp3path, NULL, 0) != 0)
        return -1; // Couldn't open file
    while(1){
        readbytes = av_read_frame(pFormatCtx, pkt);
        if (readbytes < 0){
            break;
	}
        duration += pkt->duration; // * (double) timebase;
    }
    av_free_packet(pkt);
    avformat_close_input(&pFormatCtx);
    avformat_free_context(pFormatCtx);
    return (duration);
}

/*
    int i;
    AVCodecContext *pCodecCtxOrig = NULL;
    AVCodecContext *pCodecCtx = NULL;
    AVFormatContext *pFormatCtx = NULL;
    AVCodec *pCodec = NULL;

    for(i=0; i < pFormatCtx->nb_streams; i++){
        if(pFormatCtx->streams[i]->codec->codec_type==AVMEDIA_TYPE_VIDEO) {
            videoStream=i;
            break;
        }
    }
    if(videoStream==-1){
        return -1; // Didn't find a video stream
    }
    // Get a pointer to the codec context for the video stream
    pCodecCtx=pFormatCtx->streams[videoStream]->codec;
    // Find the decoder for the video stream
    pCodec=avcodec_find_decoder(pCodecCtx->codec_id);
    if(pCodec==NULL){
        fprintf(stderr, "Unsupported codec!\n");
        return -1; // Codec not found
    }
    // Copy context
    pCodecCtx = avcodec_alloc_context3(pCodec);
    if(avcodec_copy_context(pCodecCtx, pCodecCtxOrig) != 0){
        fprintf(stderr, "Couldn't copy codec context");
        return -1; // Error copying codec context
    }
    // Open codec
    if(avcodec_open2(pCodecCtx, pCodec, NULL) < 0){
        return -1; // Could not open codec
    }
*/


/*
References:
https://wiki.wxwidgets.org/Compiling_and_getting_started
http://dranger.com/ffmpeg/tutorial01.html
http://dranger.com/ffmpeg/functions.html
https://stackoverflow.com/questions/60660228/how-to-get-an-accurate-duration-of-any-audio-file-quickly

g++ clipgui.cpp `wx-config --cxxflags --libs` -o clipgui
*/

