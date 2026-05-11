CC      ?= gcc
CFLAGS  ?= -std=c11 -Wall -Wextra -Wpedantic \
           -Wshadow -Wcast-align -Wcast-qual -Wconversion \
           -Wstrict-prototypes -Wmissing-prototypes \
           -Wfloat-equal -Wundef -Wpointer-arith -Wwrite-strings \
           -Wswitch-default -Wswitch-enum -Wunreachable-code \
           -O2 -Iinclude -D_POSIX_C_SOURCE=200809L
LDFLAGS ?=
LDLIBS  ?= -lglpk -lm

SRC_DIR := src
OBJ_DIR := obj
BIN_DIR := bin
DOC_DIR := doc

DOXYGEN ?= doxygen
DOXYFILE := Doxyfile

SOURCES := $(wildcard $(SRC_DIR)/*.c)
OBJECTS := $(SOURCES:$(SRC_DIR)/%.c=$(OBJ_DIR)/%.o)
TARGET  := $(BIN_DIR)/solveur

.PHONY: all clean mrproper run-test help doc doc-clean

all: $(TARGET)

$(TARGET): $(OBJECTS) | $(BIN_DIR)
	$(CC) $(LDFLAGS) -o $@ $^ $(LDLIBS)

$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c | $(OBJ_DIR)
	$(CC) $(CFLAGS) -c -o $@ $<

$(OBJ_DIR):
	mkdir -p $(OBJ_DIR)

$(BIN_DIR):
	mkdir -p $(BIN_DIR)

clean:
	rm -rf $(OBJ_DIR)

mrproper: clean doc-clean
	rm -rf $(BIN_DIR)

doc: $(DOXYFILE)
	$(DOXYGEN) $(DOXYFILE)

doc-clean:
	rm -rf $(DOC_DIR)

run-test: $(TARGET)
	@echo "--- Test UKP : prob_sac_1.txt ---"
	@$(TARGET) --probleme ukp --fichier "../Fichiers tests - Sac à dos-20260510/prob_sac_1.txt"
	@echo
	@echo "--- Test TSP : graphe_12.txt ---"
	@$(TARGET) --probleme tsp --fichier "../Fichiers tests - Voyageur de commerce-20260510/graphe_12.txt"

help:
	@echo "Cibles disponibles :"
	@echo "  make            -> compile $(TARGET)"
	@echo "  make clean      -> supprime les .o"
	@echo "  make mrproper   -> supprime tout (.o + binaire + doc)"
	@echo "  make run-test   -> execute deux tests rapides"
	@echo "  make doc        -> genere la documentation Doxygen dans $(DOC_DIR)/html"
	@echo "  make doc-clean  -> supprime la documentation generee"
