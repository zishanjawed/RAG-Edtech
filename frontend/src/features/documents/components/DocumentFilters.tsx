/**
 * DocumentFilters Component
 * Provides filtering, search, and tag selection for documents
 */

import { useState } from 'react'
import { DocumentFilter, DocumentFiltersState } from '../../../api/types'
import { Input } from '../../../components/ui/Input'
import { Badge } from '../../../components/ui/Badge'
import { Button } from '../../../components/ui/Button'
import { Search, X, Filter } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuCheckboxItem,
  DropdownMenuTrigger,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from '../../../components/ui/dropdown-menu'

interface DocumentFiltersProps {
  filters: DocumentFiltersState
  onFiltersChange: (filters: DocumentFiltersState) => void
  availableSubjects?: string[]
  availableTags?: string[]
}

const filterOptions: { value: DocumentFilter; label: string }[] = [
  { value: 'all', label: 'All Documents' },
  { value: 'owned', label: 'Owned by Me' },
  { value: 'shared', label: 'Shared with Me' },
]

export function DocumentFilters({
  filters,
  onFiltersChange,
  availableSubjects = ['Chemistry', 'Physics', 'Biology', 'Mathematics'],
  availableTags = [],
}: DocumentFiltersProps) {
  const [searchInput, setSearchInput] = useState(filters.search)

  const handleFilterChange = (filter: DocumentFilter) => {
    onFiltersChange({ ...filters, filter })
  }

  const handleSearchChange = (value: string) => {
    setSearchInput(value)
    onFiltersChange({ ...filters, search: value })
  }

  const handleSubjectToggle = (subject: string) => {
    const newSubjects = filters.subjects.includes(subject)
      ? filters.subjects.filter((s) => s !== subject)
      : [...filters.subjects, subject]
    onFiltersChange({ ...filters, subjects: newSubjects })
  }

  const handleTagToggle = (tag: string) => {
    const newTags = filters.tags.includes(tag)
      ? filters.tags.filter((t) => t !== tag)
      : [...filters.tags, tag]
    onFiltersChange({ ...filters, tags: newTags })
  }

  const handleClearFilters = () => {
    onFiltersChange({
      filter: 'all',
      search: '',
      subjects: [],
      tags: [],
    })
    setSearchInput('')
  }

  const hasActiveFilters =
    filters.filter !== 'all' ||
    filters.search !== '' ||
    filters.subjects.length > 0 ||
    filters.tags.length > 0

  return (
    <div className="space-y-4">
      {/* Main filter tabs */}
      <div className="flex items-center gap-2">
        <div className="inline-flex rounded-lg border p-1 bg-muted/50">
          {filterOptions.map((option) => (
            <Button
              key={option.value}
              variant={filters.filter === option.value ? 'default' : 'ghost'}
              size="sm"
              onClick={() => handleFilterChange(option.value)}
              className="relative"
            >
              {option.label}
            </Button>
          ))}
        </div>
      </div>

      {/* Search and advanced filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        {/* Search input */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
          <Input
            type="text"
            placeholder="Search documents by title, subject, or tags..."
            value={searchInput}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="pl-10 pr-10"
          />
          {searchInput && (
            <Button
              variant="ghost"
              size="sm"
              className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7 p-0"
              onClick={() => handleSearchChange('')}
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>

        {/* Subject filter dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm" className="min-w-[140px]">
              <Filter className="h-4 w-4 mr-2" />
              Subjects
              {filters.subjects.length > 0 && (
                <Badge variant="secondary" className="ml-2 h-5 min-w-5 px-1.5">
                  {filters.subjects.length}
                </Badge>
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuLabel>Filter by Subject</DropdownMenuLabel>
            <DropdownMenuSeparator />
            {availableSubjects.map((subject) => (
              <DropdownMenuCheckboxItem
                key={subject}
                checked={filters.subjects.includes(subject)}
                onCheckedChange={() => handleSubjectToggle(subject)}
              >
                {subject}
              </DropdownMenuCheckboxItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Tags filter dropdown (if tags available) */}
        {availableTags.length > 0 && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="min-w-[120px]">
                <Filter className="h-4 w-4 mr-2" />
                Tags
                {filters.tags.length > 0 && (
                  <Badge variant="secondary" className="ml-2 h-5 min-w-5 px-1.5">
                    {filters.tags.length}
                  </Badge>
                )}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-48">
              <DropdownMenuLabel>Filter by Tags</DropdownMenuLabel>
              <DropdownMenuSeparator />
              {availableTags.slice(0, 10).map((tag) => (
                <DropdownMenuCheckboxItem
                  key={tag}
                  checked={filters.tags.includes(tag)}
                  onCheckedChange={() => handleTagToggle(tag)}
                >
                  {tag}
                </DropdownMenuCheckboxItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        )}

        {/* Clear filters */}
        {hasActiveFilters && (
          <Button variant="ghost" size="sm" onClick={handleClearFilters}>
            <X className="h-4 w-4 mr-2" />
            Clear
          </Button>
        )}
      </div>

      {/* Active filters display */}
      {hasActiveFilters && (
        <div className="flex flex-wrap gap-2">
          {filters.subjects.map((subject) => (
            <Badge key={subject} variant="secondary" className="gap-1">
              {subject}
              <button
                onClick={() => handleSubjectToggle(subject)}
                className="ml-1 hover:bg-muted-foreground/20 rounded-full"
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
          {filters.tags.map((tag) => (
            <Badge key={tag} variant="outline" className="gap-1">
              {tag}
              <button
                onClick={() => handleTagToggle(tag)}
                className="ml-1 hover:bg-muted-foreground/20 rounded-full"
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
        </div>
      )}
    </div>
  )
}

