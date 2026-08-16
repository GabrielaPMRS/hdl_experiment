module example;

    int lo, med, hi;
    bit result;
    int selected;

    initial begin
        lo = 20;
        med = 224;
        hi = 164;

        result = (lo < med < hi);

        if (result)
            selected = med;
        else
            selected = hi;
    end

endmodule

correct answer: result = 1, selected = 224