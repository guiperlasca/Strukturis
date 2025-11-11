export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "13.0.5"
  }
  public: {
    Tables: {
      document_exports: {
        Row: {
          created_at: string
          csv_url: string | null
          document_id: string
          id: string
          json_url: string | null
        }
        Insert: {
          created_at?: string
          csv_url?: string | null
          document_id: string
          id?: string
          json_url?: string | null
        }
        Update: {
          created_at?: string
          csv_url?: string | null
          document_id?: string
          id?: string
          json_url?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "document_exports_document_id_fkey"
            columns: ["document_id"]
            isOneToOne: false
            referencedRelation: "documents"
            referencedColumns: ["id"]
          },
        ]
      }
      document_pages: {
        Row: {
          confidence: number | null
          created_at: string
          document_id: string
          entities: Json | null
          id: string
          page: number
          quality_hints: Json | null
          status: string
          tables: Json | null
          text: string | null
        }
        Insert: {
          confidence?: number | null
          created_at?: string
          document_id: string
          entities?: Json | null
          id?: string
          page: number
          quality_hints?: Json | null
          status: string
          tables?: Json | null
          text?: string | null
        }
        Update: {
          confidence?: number | null
          created_at?: string
          document_id?: string
          entities?: Json | null
          id?: string
          page?: number
          quality_hints?: Json | null
          status?: string
          tables?: Json | null
          text?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "document_pages_document_id_fkey"
            columns: ["document_id"]
            isOneToOne: false
            referencedRelation: "documents"
            referencedColumns: ["id"]
          },
        ]
      }
      documents: {
        Row: {
          created_at: string
          id: string
          mime_type: string
          original_url: string
          status: string
          total_pages: number
          user_id: string
        }
        Insert: {
          created_at?: string
          id?: string
          mime_type: string
          original_url: string
          status?: string
          total_pages?: number
          user_id: string
        }
        Update: {
          created_at?: string
          id?: string
          mime_type?: string
          original_url?: string
          status?: string
          total_pages?: number
          user_id?: string
        }
        Relationships: []
      }
      ocr_documents: {
        Row: {
          completed_at: string | null
          created_at: string
          detected_language: string | null
          document_type: string | null
          error_message: string | null
          file_size: number | null
          id: string
          mime_type: string | null
          original_filename: string
          overall_confidence: number | null
          processing_time_ms: number | null
          status: string
          storage_path: string
          total_pages: number | null
          user_id: string | null
        }
        Insert: {
          completed_at?: string | null
          created_at?: string
          detected_language?: string | null
          document_type?: string | null
          error_message?: string | null
          file_size?: number | null
          id?: string
          mime_type?: string | null
          original_filename: string
          overall_confidence?: number | null
          processing_time_ms?: number | null
          status?: string
          storage_path: string
          total_pages?: number | null
          user_id?: string | null
        }
        Update: {
          completed_at?: string | null
          created_at?: string
          detected_language?: string | null
          document_type?: string | null
          error_message?: string | null
          file_size?: number | null
          id?: string
          mime_type?: string | null
          original_filename?: string
          overall_confidence?: number | null
          processing_time_ms?: number | null
          status?: string
          storage_path?: string
          total_pages?: number | null
          user_id?: string | null
        }
        Relationships: []
      }
      ocr_pages: {
        Row: {
          confidence: number | null
          corrected_text: string | null
          created_at: string
          detected_language: string | null
          document_id: string
          has_table: boolean | null
          id: string
          page_number: number
          raw_text: string | null
          table_data: Json | null
        }
        Insert: {
          confidence?: number | null
          corrected_text?: string | null
          created_at?: string
          detected_language?: string | null
          document_id: string
          has_table?: boolean | null
          id?: string
          page_number: number
          raw_text?: string | null
          table_data?: Json | null
        }
        Update: {
          confidence?: number | null
          corrected_text?: string | null
          created_at?: string
          detected_language?: string | null
          document_id?: string
          has_table?: boolean | null
          id?: string
          page_number?: number
          raw_text?: string | null
          table_data?: Json | null
        }
        Relationships: [
          {
            foreignKeyName: "ocr_pages_document_id_fkey"
            columns: ["document_id"]
            isOneToOne: false
            referencedRelation: "ocr_documents"
            referencedColumns: ["id"]
          },
        ]
      }
      profiles: {
        Row: {
          avatar_url: string | null
          company: string | null
          created_at: string
          full_name: string | null
          id: string
          updated_at: string
        }
        Insert: {
          avatar_url?: string | null
          company?: string | null
          created_at?: string
          full_name?: string | null
          id: string
          updated_at?: string
        }
        Update: {
          avatar_url?: string | null
          company?: string | null
          created_at?: string
          full_name?: string | null
          id?: string
          updated_at?: string
        }
        Relationships: []
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {},
  },
} as const
